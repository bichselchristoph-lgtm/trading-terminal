---
id: 046
title: A committed permission policy — and the measurement of whether it binds
type: task
class: admin
version: 1.0
unblocks: NOTHING. No product task. See "Rule 16, and what this task cannot claim" — the honest answer is recorded rather than a plausible one invented
owner: claude-code
author: claude-code (self-authored, under CLAUDE.md v1.7 "Who may decide")
tree: D:\Dev\momentum
---

**Status** DONE

# 046 — a committed permission policy

**Type: rule change and bug. Class: admin.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/046-for-code-task-permission-policy.md` exists in your tree and
`handoff/done/046-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

---

## This file was written AFTER the work, and that is a departure

**Stated first because it is the least comfortable thing in the file.**

`CLAUDE.md` v1.7 permits Claude Code to author its own `class: admin` task file and act on it in
the same session. **This file was not written in the same session. It was written after three
commits had already landed** — `58b0926`, `f35bd3a`, `e2e3a93` — and after they had been pushed.

**So the file is a record, not an authorisation, and it never was one.** Guardrail 4 ("review
moves after, not before") is unaffected: the design session still reads the done-note and may
still reject. Guardrail 1 (`class: admin` only) holds. **Guardrail 2 does not hold and the next
section says so.**

**Why write it at all.** `NOW.md` derives `done` from a file existing in `handoff/done/`, and
rule 16's admin:product ratio counts `class:` across task files. **Work that lands with no task
file is work the status board cannot see and the tax cannot count** — which is the precise
failure rule 16 exists to make visible. A retroactive file is worse than a timely one and much
better than none.

---

## Rule 16, and what this task cannot claim

**Guardrail 2 requires a self-authored admin task to name the product task it unblocks. This one
cannot, and no product task is named.**

The closest honest statements, none of which is "unblocks":

- The `deny` on `git clean` is the only rule that stands between a session and `records/tape/` —
  **2 GB of 2026-08-11 QQQ capture that cannot be re-recorded**, and which Layer 0 row 14 cites
  as its basis. **That is protection, not unblocking.** No product task is waiting on it.
- The worktree and uncommitted-work denies protect whatever a *concurrent* session is holding.
  Again: protection.

**A protection is not an unblocking, and stretching the word to fit is exactly the move rule 16
exists to prevent.** Recorded here as a rule-16 miss rather than dressed up.

**Consequence, stated so it is watched:** had this task been authored *before* the work, under
`045` Part 4's gate, **guardrail 2 would have refused it.** It is admin that unblocks nothing.
The work still looks right — it removes a route by which uncommitted work and unrepeatable data
are destroyed — but "looks right" is the argument every piece of admin makes. **The design
session may reject on this ground alone and that would be a correct application of the rule.**

---

## Numbering

**Read from `handoff/inbox/`, not inferred.** Highest present was `045`; `046` was free in both
`handoff/inbox/` and `handoff/done/`. **The commits' own comments said `044` until the inbox was
read** — the id-collision shape `OBS-052` and `OBS-062` already record, caught here before it
landed.

---

## Part 1 — the policy exists and is committed

`.claude/settings.json` is the shared permission policy: **broad on reads and repo-local writes,
narrow on deletion and on anything outside `D:\Dev`.**

- **`allow` names only paths under `D:\Dev\momentum` and read-only verbs**, so everything outside
  is narrow **by absence** rather than by a forbidden-list. Not allowed ⇒ it prompts. **A
  forbidden-list grows into a hiding place**; absence does not.
- **Nothing in `allow` can incur external cost.** `~/.claude/hooks/spend_guard.py` keeps its job
  intact.
- **`deny` covers** `git clean` (the only command that removes `records/tape/`), the force-push
  forms, writes to `christoph/done/` and `christoph/open/`, `.claude/worktrees/`, the Drive
  from-folders, the archive tree, and — **enforcing standing rules that had never been
  structural** — `~/.claude/spend_limits.yaml`, `~/.claude/spend_daily.jsonl` and `hooks/`.

**The `.gitignore` guard is narrowed, not gutted.** One negation naming an exact filename,
placed after the blanket `.claude/**/*.json` rule because that is the only position git honours.
**`settings.local.json` — one word from the permitted name, and where the predecessor's live
Databento key sat — stays ignored.**

---

## Part 2 — measure whether it binds, and do not assume

**`allow`/`ask`/`deny` are not equally load-bearing and nothing in this repo had ever measured
which of them binds.** Probe each class against the running session:

| class | probe | expected |
|---|---|---|
| `deny` on a path | read a `.env`-shaped path | blocked |
| `deny` on a shell | `git clean -n -d` | blocked |
| `ask` on a shell | a command matching `ask` and **not** the exact `allow` | prompted |

**Choose the third probe so it matches `ask` and misses `allow`.** A probe that both permit
proves nothing — `git push origin main` succeeding proves nothing, because pushes were
unprompted before the file existed.

**If `ask` does not bind, every protection sitting in `ask` is decorative**, and the irreversible
set must move to wherever binding is *verified*, not wherever it reads best.

---

## Part 3 — say where prefix matching leaves gaps, and do not paper over them

A rule is a **prefix** match. **Enumerate the reachable spellings that step around each
irreversible rule** and state, per gap, what actually covers it. **Do not claim coverage a
prefix does not give.**

---

## Part 4 — structural, not remembered

Standing rule 4: a rule that lives in one session's context is a rule the next session breaks.
**Every claim above that can be asserted, is asserted, and every new test is seen RED first.**

---

## Not in scope

No changes to `spend_guard.py` or its patterns. No widening of the `.claude/` ignore guard beyond
one exact filename. No product work of any kind.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | full suite, **not a targeted run** |
| **Refusal** | Claude Code | each new guard seen red against the exact mutation it exists to catch |
| **Measured** | Claude Code | the three probes of Part 2, with the observed result — not the expected one |

---

## Report

1. The three probe results, **as observed**.
2. Which rules moved class as a result, and why that class.
3. **Every prefix gap found**, and what covers it instead.
4. What the full suite said that a targeted run did not.
5. **What this task cannot claim under rule 16.**
6. What you could not do. Empty is suspicious.

---
id: 031
title: Two sessions, one tree — make the blanket commit impossible rather than discouraged
type: infrastructure
owner: claude-code
depends: 023
---

**Status** WRITTEN

# 031 — The tree now has two writers and nothing knows it

**Run before `017`.** A remote makes this sharper, not safer: a push can now carry another
session's half-finished work off the machine, where it is no longer only a local mess.

---

## The evidence, observed on 2026-08-13

Christoph began running **two Claude Code terminals in one tree** — A holding a six-hour live
capture, B working the inbox in sequence. Within four hours:

1. **B's `git add -A` swept in `tools/probe_keepuptodate_scale.py`** — A's 406-line probe,
   written three minutes earlier. It was committed under a message that said nothing about it.
2. **B then ran `git rm --cached` on it**, which pulled the file back out of *A's* index. B
   called this "the wrong call made for a reason that looked right." Nothing was lost. **Nothing
   was lost because A noticed**, which is not a mechanism.
3. **The suite count moved four times while one done-note was being written** — 236/2, 273/2,
   274/3, 278/2. B stopped quoting a figure and pointed at `verify-output.txt` instead.
4. **`verify.ps1` cannot tell one session's changes from another's.** Section 2 lists
   uncommitted paths and attributes none of them.

**The diagnosis is separate from the observations above, and it is this:** the handoff protocol
was written for one writer. Every mechanism in it — the adoption gate, the verification gate,
copy-and-keep — assumes that the tree between a note and its `verify.ps1` run changed only
because of the task the note describes. **With two sessions that assumption is simply false, and
nothing detects when it breaks.**

**B's instinct in (3) was correct and should become the rule, not a habit.**

---

## The construction: a lease, because a rule in prose will be broken

**Do not add a paragraph to `CLAUDE.md` telling sessions to be careful.** This project has
learned repeatedly that a convention living in prose depends on someone remembering, and both
sessions here *were* being careful. **B believed it was complying while it swept another
session's file into a commit.**

### Part 1 — the lease

A file at the repo root, **gitignored**, named `.commit-lease`:

```yaml
holder:     "terminal-B"        # whatever the session calls itself; free text
task:       "028"
acquired:   "2026-08-13T15:04:11-04:00"
scope:                          # globs this session may stage. REQUIRED, no default
  - "docs/specs/**"
  - "docs/observations/**"
  - "tests/test_regime_prompt_invariants.py"
```

**Acquired before the first `git add` of a task. Released after the commit.** A session that
finds a live lease held by someone else **does not stage and does not commit.** It still reads,
runs tests, and writes files — **the lease governs the index, not the disk.** That distinction
is the whole design: A can capture for six hours and write whatever it likes; it simply does not
own the index while B does.

**`scope` is required and has no default** (`SPEC.md` §4.4). A lease with no scope is refused.
**A lease claiming `**` is refused** — a wildcard scope is the blanket add wearing a hat.

**A stale lease is reported, never silently broken.** Older than 60 minutes: print the holder,
the task and the age, and **refuse**. Breaking it is a deliberate act with a flag, and the flag
is named in the output so the next person can find it. **60 minutes is a decision made here, not
sourced — `source: task_decision_2026-08-13`, PROVISIONAL.** A six-hour capture that never
stages will not trip it because it never holds the lease at all.

### Part 2 — the hooks, which are where the enforcement actually lives

`.githooks/pre-commit`, wired via `core.hooksPath` so it is versioned and arrives with a clone:

- **No lease → refuse.**
- **Lease held by another holder → refuse**, naming them.
- **Any staged path outside `scope` → refuse, and list the offending paths.** *This is the check
  that would have caught `023`.*

`.githooks/pre-push`:

- **Refuse if the working tree has uncommitted changes outside the current lease's scope.**
  A push under a foreign lease is the failure mode a remote introduces.

**The hook is the mechanism. The lease is only its input.** A hook that warns and proceeds is a
rule in prose with extra steps.

### Part 3 — `verify.ps1` gains a sixth fact

It currently states **five facts and draws no conclusion**. It will state **six**. *Say the count
changed and why in the done-note* — a number that moves silently through documents is this
project's most-repeated defect, and this document is amending the header that names it.

> **6. LEASE — who owns the index right now**
> `free` · or holder, task, age. **No opinion, as with the other five.**

**Also: section 2's uncommitted paths get one line above them** stating that they are
**unattributed** — `verify.ps1` cannot tell whose they are, and a reader who assumes otherwise
draws exactly the wrong conclusion from a dirty tree.

### Part 4 — one line in the protocol, because a note quoted a moving number

`docs/specs/HANDOFF-PROTOCOL.md`, bumped a version:

> **A done-note never quotes a test count.** It states that `verify.ps1` ran and when. **The
> count belongs to `verify-output.txt`, which is a single observation of a tree that may have
> two writers.** *(B did this correctly on 2026-08-13 before there was a rule; the rule exists
> so the next session does not have to work it out.)*

---

## What this deliberately does **not** do

- **It does not stop two sessions running.** That is a useful pattern — a six-hour capture
  alongside inbox work is exactly right, and today it worked.
- **It does not attribute file changes.** Nothing here can tell which session wrote a file on
  disk. **The lease governs the index only, and the done-note must not claim more.**
- **It does not touch `christoph/`.**

---

## Done when

- The lease is acquired and released across at least one real task.
- **The pre-commit hook has been seen refusing** — demonstrate all three: no lease, foreign
  lease, out-of-scope path. **Quote each refusal.**
- A test asserts the hook refuses an out-of-scope path. **Seen red first**, with the hook
  disabled.
- A test asserts a wildcard scope is refused.
- `verify.ps1` prints six sections and the unattributed line.
- `HANDOFF-PROTOCOL.md` carries the no-test-count rule and a new version row.

---

## Deliverable

`handoff/done/031-for-code-two-sessions-one-tree.md`:

1. The three refusals, quoted verbatim.
2. The out-of-scope test red, then green.
3. The `verify.ps1` header change, and confirmation the done-note says five became six.
4. **Whether the 60-minute staleness bound is right**, having used it. It is a guess.
5. **What you could not do**, and why. Empty is suspicious.
6. `verify.ps1` run at `<time>`. Do not quote its output — HANDOFF-PROTOCOL v1.2.

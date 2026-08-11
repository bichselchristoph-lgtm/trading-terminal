---
id: 013a
title: Where did the done-notes go? — read-only handoff tree inventory
status: DONE
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
written: retrospectively under 013c §4a — 013a's own exit test forbade writing this file
---

# 013a — handoff tree inventory

**Status** DONE

> **This note was written after the fact, under `013c` §4a.** `013a`'s Green exit test required
> the working tree to hash identically before and after, which made writing a done-note a
> violation of the task's own exit test. The findings therefore lived only in chat until now.
> **Nothing below was re-derived by re-running anything** — it is the report as given.

---

## The premise was wrong

`013a` opened: *"That folder holds **one item**, while six tasks … have completed."*

**`handoff/done/` held 20 files**, tracked in HEAD, added across five commits — `ab36695`,
`015a74d`, `c634416`, `0e0a2ff`, `f9c18c6`, `aa8bb43`.

**Done-notes had been stored on disk all along.** Every one of H8, H9, H9a, M001, H10, H11
had a note in `handoff/done/`, plus 005, 008a, 008b, 012a, 013, the four 004-series, and three
older notes. The claim that *"no done-note has ever been stored on disk"* was not the case in
this repository.

## The convention has never once been exercised as a move

```
git log --diff-filter=R -M -- handoff/   →   (empty)
```

**No file has ever been moved from `inbox/` to `done/`.** A done-note is *created* in
`handoff/done/` as a new file; the inbox task file stays. Both copies exist for every
completed task, by design.

Not unexercised, and not violated — **a third thing**: a copy-and-keep convention nobody had
written down. It is now written down, in `HANDOFF-PROTOCOL.md` under 013c §2c.

## The six task files

| task | path on disk |
|---|---|
| H8 | `handoff/inbox/H8-regime-snapshot-path.md` |
| H9 | `handoff/inbox/H9 — Commit the specs into the repo.md` |
| **H9a** | **ABSENT — no task file anywhere in this repo or in `momentum-harness`** |
| M001 | `handoff/inbox/M001-new-repo-and-adoption-gate.md` |
| H10 | `handoff/inbox/H10-regime-prompt-v1.2.md` |
| H11 | `handoff/inbox/H11-resupply-rule-and-schema-fix.md` |

Also found: **`H9-v3-specs-into-new-tree.md` exists only in `momentum-harness`**, never carried
into this tree, while the v2 file is the one in this inbox. That absence is why H9 was built
from v2 and missed most of v3.

### H9a's instructions are unrecoverable — a closed gap

*(Settled after the original report; recorded here because it cannot be reopened.)*

**H9a's task file never existed**, and its instructions are gone. `docs/PROVENANCE.md` and
H9a's own done-note survive, so the *output* is inspectable — but **what H9a actually asked
for is absent from both repositories and from every project artifact.**

The consequence, stated plainly: **if anyone later asks whether the 183-file inventory
answered the question it was set, there is no way to check.** The done-note records what was
built to — M001's four references to H9a, plus instructions given directly — and says as much
in its own opening. That is the closest thing to a specification that exists.

This is a closed gap, not an open one. Nothing can recover it.

## Where done-note text survives

| hash | found in |
|---|---|
| `e7d3a14`, `66994a8`, `f9c18c6` | `handoff/done/H10-regime-prompt-v1.2.md` |
| `aa8bb43` | nowhere but 013a's own task file — it was HEAD, cited by no note yet |
| `1afcecf` | four done-notes |

The notes do retain their own commit references.

## What the docs claim — quoted

`CLAUDE.md`:

> **132** ``| `handoff/inbox/NNN-*.md` | Build tasks. Written by chat, addressed to this session. |``
> **133** ``| `handoff/done/NNN-*.md` | One per completed task: what changed, what the tests said, what you found. |``
> **136** ``| `handoff/*.md` (root) | A **standing instruction that is always live**. Not a task; never moves to `handoff/done/`. |``
> **141** ``handoff/done/NNN-*.md`` must be **readable cold** by someone with no session context…

`docs/specs/HANDOFF-PROTOCOL.md` — **one line only, at the time of the read**:

> **68** Every `.md` in `handoff/inbox/` and `handoff/done/` declares, in its header:

**No spec stated where a done-note is stored.** `CLAUDE.md:133` was the only line in the
repository saying a completed task produces a file in `handoff/done/`, and it never said
whether the inbox file moves. 013c §2c has since fixed that in `HANDOFF-PROTOCOL.md`.

## Was 013 running concurrently?

**Yes — and it had already changed this tree before 013a read it.** Not as a separate
process, but its changes were staged and uncommitted: 15 handoff paths dirty, 9 modified by
the state-header backfill and 6 added.

**Consequence:** every mtime in the tree listing read `2026-08-11 11:01–11:12` and reflected
013's backfill, not original authorship. **Any conclusion drawn from mtimes in that listing
would have been wrong.**

## Proof the tree was unchanged

```
baseline sha256 (before 013a) : fe028cd91e2f870ab80838f44657afe4
current  sha256 (after)       : fe028cd91e2f870ab80838f44657afe4
UNCHANGED: True     27 entries, handoff/ still 37 files
```

Nothing created, moved, renamed or deleted. `HANDOFF-PROTOCOL.md` untouched. Nothing
committed. `records/` and the capture untouched.

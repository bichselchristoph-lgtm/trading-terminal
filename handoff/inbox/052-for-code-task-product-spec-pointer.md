---
id: 052
title: The product-spec pointer, the document-link audit, and the mockup-citation sweep
type: task
class: admin
version: 3.0
originates: PROCESS-SPEC §8a · project instructions rules 21 and 22
closes: B-085
unblocks: NOTHING — pointers and hygiene. Stated honestly rather than dressed up.
depends: none
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 052 — the pointer, the link audit, and the mockup sweep

**Type: task. Class: admin.** No behaviour changes. **A header comment, and two greps.**

**v3.0 adds Part 3.** If more than one version of this file exists, **v3.0 is the one to take.**

---

## Addressing

**If `handoff/inbox/052-for-code-task-product-spec-pointer.md` exists in your tree and
`handoff/done/052-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes. **Scratch in `$env:TEMP`, never the repo.**

---

## Background — three conventions changed on 2026-08-16

**You do not need to agree with them; you need to know they exist, because the tree still reflects
the old ones.**

**1. Two spec systems, both authoritative in their own domain.**

| | Product spec | Dev spec |
|---|---|---|
| **Where** | Google Docs, `Trading Terminal` folder | **`docs/specs/SPEC.md` and siblings** |
| **Authoritative for** | **Product** — behaviour, refusals, meaning, bases, what renders | **Dev** — implementation, structure, the code-ready statement of a slice |
| **Read by** | Christoph, the design session | **You** |

**A dev spec is derived from a product spec. The derivation runs one way only.** Where they disagree
about product behaviour the product spec wins and `SPEC.md` is corrected; where they disagree about
implementation `SPEC.md` wins — **and a product spec that specified implementation had overstepped.**

**2. Nothing is referenced by document link.** A revision creates a new document, so **a document link
dies on every revision while a name does not.** Reference is by name plus folder. **A link that
resolves to a superseded document is worse than one that fails.**

**3. Mockups are named, not numbered.** `mockup-14-modes-whole-screen.html` is now
`UI mockup — whole screen in each mode - LATEST.html`. **The number said nothing about which spec a
mockup served or whether it was current.**

---

## Part 1 — the header comment

**Add this at the very top of `docs/specs/SPEC.md`**, above the existing title, exactly as written:

```
<!--
DEV SPEC — authoritative for implementation.

This document is NOT the product specification. Product behaviour — what a panel
shows, what a number means, which basis a statistic takes, what refuses and how —
is owned by the product spec set:

  Google Drive folder: Trading Terminal
  https://drive.google.com/drive/folders/1rHQ9_46N2yhyKJg6Qd6iCnDTDx2Y8TCN

  Documents are referenced BY NAME, never by document link. The current version of
  each carries "- LATEST" in its title; superseded copies carry "- OLD" and live in
  Old spec versions/. Start at SPEC-INDEX, which names which spec owns which fact.

A dev spec is DERIVED FROM a product spec. The derivation runs one way only.
Where this document and a product spec disagree about product behaviour, the
product spec wins and this document is corrected. Where they disagree about
implementation, this document wins.

Ruled 2026-08-16. See PROCESS-SPEC section 8a. Bug row B-085.
-->
```

**Add the same comment, unchanged, to `docs/specs/BUILD-PLAN.md` and `docs/specs/RE-SUPPLY.md`** if
those files exist.

**Do not add it to `REGIME-PROMPT.md` or `HANDOFF-PROTOCOL.md`.** Those are neither dev specs nor
product specs — one is an instruction to a scheduled run, the other is protocol.

---

## Part 2 — the document-link audit

**Grep the tree for:**

```
docs.google.com/document
docs.google.com/spreadsheets
drive.google.com/file
```

**Across `handoff/`, `christoph/`, `docs/`, `claude/` and `CLAUDE.md`.**

**Report every hit with file and line.**

### What to fix

**Only files that are still live instructions:** `CLAUDE.md`, anything in `handoff/inbox/` not yet
done, `docs/specs/*`, and `claude/NOW.md` if it carries any.

**Replace each with the document name plus the folder:**

```
SPEC-INDEX, in the Trading Terminal folder on Google Drive
```

**One folder link is permitted and only one** — the Trading Terminal folder, as it appears in the
Part 1 header. **A folder link survives revisions; a document link does not.**

### What NOT to touch

**Do not rewrite links in `handoff/done/`, `handoff/accepted/`, or `docs/observations/`.** Those are
records of what was true at the time. **Correcting a record is not the same as correcting a rule.**

---

## Part 3 — the mockup-citation sweep

**Mockups no longer have numbers.** Anything in the tree citing `mockup-NN` now names an artifact that
does not exist under that name.

**Grep for:**

```
mockup-
mockup 
```

**Across the same paths as Part 2.**

### The mapping

| Old | New |
|---|---|
| `mockup-08-tape-states` | `TAPE mockup — twelve tape states` |
| `mockup-10-level-rail-sortings` | `LEVELS mockup — the rail and its sortings` |
| `mockup-12-core-surface-panels` | `UI mockup — core surface panels` |
| `mockup-13-modes-live-locked-paper` | `RISK mockup — live, locked and paper modes` |
| `mockup-14-modes-whole-screen` | `UI mockup — whole screen in each mode` |
| `mockup-15-risk-and-the-lock` | `RISK mockup — the panel and the lock` |
| `mockup-16-colour-budget` | `UI mockup — the colour budget` |
| `mockup-17-colour-links` | `UI mockup — link colour` |
| `mockup-09` · `mockup-11` | **Superseded by `UI mockup — core surface panels`** |
| `mockup-01` · `02` · `03` · `04` · `05` · `07` · `core-workflow` | **First generation. Not in Drive. See MOCKUP-INDEX** |

**Same rule as Part 2: fix live instructions, leave records alone.**

**A citation to a first-generation mockup is a finding, not a rename.** Those predate Textual, the
TRADE consolidation and three deleted features — **if a live instruction still cites one, the
instruction is probably stale in more than its filename. Report it rather than patching the name.**

---

## What NOT to do

**Do not move, split, rename or restructure any file in `docs/specs/`.** Retiring that folder was
discussed and **rejected**.

**Do not copy any product spec into the tree.** They live in Drive and are authoritative there.
**A second copy is a second authority.**

**Do not reconcile `SPEC.md` against the product specs in this task.** That is real and larger work —
**`SPEC.md` grew organically and contains architecture, behaviour and rationale interleaved**, and
some of its product statements are now owned elsewhere. **Finding them needs the ruling to exist
first, which is what Part 1 is for.**

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise.
**Then run the export, from the main checkout** — not from a worktree.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | The suite still passes. **Nothing here should change behaviour, so a red is a finding about coupling, not about this task** |
| **Refusal** | Claude Code | **Not applicable — no rendering path is touched. State that explicitly rather than inventing one** |
| **UAT** | Christoph | None. **An admin task with `unblocks: NOTHING` does not earn a UAT** |

---

## Report

1. **Which files received the header comment**, and which did not, with the reason.
2. **Whether `RE-SUPPLY.md` and `BUILD-PLAN.md` exist** at the stated paths.
3. **Every document link found**, with file and line — including ones you did not change.
4. **Every `mockup-NN` citation found**, with file and line, and which you rewrote.
5. **Any live instruction citing a first-generation mockup** — a staleness finding, reported not
   patched.
6. **Any file in `docs/specs/` you judge to be neither a dev spec nor protocol** — a classification
   finding, worth reporting rather than deciding.
7. **Bug row to update: B-085 → CLOSED BY DESIGN.** Report the row id and target status; do not
   assume the sheet was updated.
8. **What you could not do**, and why. Empty is suspicious.

---
id: 029
title: Tasks 006 and 007 render as ready and must not run
type: decision
bug: OBS-076
blocks: two tasks currently showing as runnable on the board
---

**Status** OPEN

# 029 — do 006 and 007 still stand?

## The question

**Both cite a first-generation mockup. Do their visual contracts still hold?**

## Why this is urgent rather than tidy

**`NOW.md` renders them as `ready now`.** A session that picks them up will build to a screen design
that predates **Textual, the TRADE consolidation, the deletion of the conviction dial, and the
deletion of the regime surface.**

**The design session tried to write a staleness banner into both files and was correctly refused** —
they are evidence-carried and hash-verified against `momentum-harness`, so editing them broke
`test_evidence_carry_intact.py`. **A hash-verified file is immutable by construction, so the warning
cannot live inside it.** This file is where it lives instead.

## What you are ruling on

**Not the filenames — the pictures.** Whether what those tasks say the screen should look like is
still what you want.

## My recommendation

**Retire both and re-cut them from the current mockups when their slices come up.**

**Their refusal grammar is probably still right** — *age is shown, never enforced* has survived every
revision. **Their layout is two generations old**, and re-cutting is cheaper than auditing which half
of a task is still true.

## To answer

Retire, or keep with the contract confirmed. Copy this file to `christoph/done/` with the date.

**Until then they should not be run**, and that is now visible on the board rather than remembered.
Christoph Aug 22, 2026: retire both, re-cut from current mockups when the slices come up.
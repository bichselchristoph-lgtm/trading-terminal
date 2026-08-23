---
id: 065-q1
title: Part A names three missing levels; the exit test needs thirteen more that do not exist anywhere in the tree
status: OPEN
raised_by: claude-code
task: 065
---

**Status** RUNNING
**Raised by** 065
**Blocks** yes — Part A's caption/refusal-caption exit tests and the UAT that reads them.

# `065` Part A's premise and its own exit test point at two different amounts of work

**I did not build a new levels panel, and I did not guess which of the two readings below
is wanted.**

---

## What `065` Part A says, and what is actually in the tree

Part A's instruction is unambiguous about scope: *"Render the three levels into the existing
rail structure and change nothing else about it."* Its premise is that twenty levels already
render and three are missing: ORL5, ORL15, 52wL.

**Checked directly, not inferred:** `core/indicators/context.py`'s `level_rail()` already
computes and has always returned `ORL5`, `ORL15` and `52wL` (confirmed by reading the function
and by running a live fixture attach — all three come back with real values, correct basis
labels, and correct provenance strings, not placeholders). `live/tui/app.py`'s `RAIL_ORDER`
already lists all three, and `context_rows()` already renders any key present in `a.rail`. The
existing test `live/tests/test_attach.py::test_a_clean_attach_fills_the_context_block` already
asserted `ORL5` and `ORL15` were present (it did not check `52wL` explicitly — I added that
assertion in this task, since it cost nothing and the ruling names it as intentional). **The
full `live/` suite (153 tests before this task, 155 after) is green with all three already
rendering.** None of this needed a code change.

**What genuinely does not exist anywhere in `core/` or `live/`:** `HOD`, `LOD`, `PDO`, `PDC`,
`PWH`, `PWO`, `PWL`, `PWC`, `MoMH`, `MoMO`, `MoML`, `MoMC`, `ATH` — thirteen of the twenty-three
levels Part A's own table names. `level_rail()`'s signature does not even take the inputs these
would need (a prior week's daily bars grouped by week, a prior month's grouped by month, today's
own RTH-sliced high/low). Only ten real levels exist today: `PDH`, `PDL`, `PMH`, `PML`, `ORH5`,
`ORL5`, `ORH15`, `ORL15`, `52wH`, `52wL` (plus `round`, which is not a level).

**The two readings genuinely disagree on how much work this is:**

1. **Part A is a no-op**, because the three named levels already render, and the "twenty
   levels" the task believed already existed is a stale count from before whatever
   already-landed change put `ORL5`/`ORL15`/`52wL` into `level_rail()`. Under this reading
   `023` levels never existed in the tree and the caption asks for a count nothing here
   produces.
2. **Part A's real scope is the other thirteen levels**, which the task's own instruction text
   ("render the three levels... change nothing else") explicitly forecloses, but which its exit
   test (`23 of 23`, `17 of 23`, all six windows) requires. All thirteen are derivable from data
   already fetched — `PDO`/`PDC` from the same `prev_day` bar `PDH`/`PDL` already use; `HOD`/`LOD`
   from an RTH slice of `today`, the same way `premarket`/`opening_5`/`opening_15` are already
   sliced; `PWH`/`PWO`/`PWL`/`PWC` and `MoMH`/`MoMO`/`MoML`/`MoMC` by grouping the already-fetched
   1-year `rth_dailies` series by ISO week and by month; `ATH` per the codebase's own existing
   ruling comment, capped at the same 52-week window as `52wH` (*"52wH/52wL/ATH are the top of the
   composition chain: the year is the ceiling"*) — so **no new IBKR request is needed either
   way**, which is the one hard constraint both readings could satisfy.

**Neither reading is mine to pick.** Reading 1 makes the caption and refusal-caption exit tests
(`23 of 23` / `17 of 23`) permanently unbuildable as specified. Reading 2 is a real, if
data-cheap, product surface — thirteen new rendered numbers, new refusal states for each, and
the fewer-available-vs-nothing-more-here distinction the task calls out — that Part A's own
instruction text explicitly says is out of scope. Building it on my own judgment would be
exactly the kind of undiscussed expansion this project's conventions exist to stop; not building
it leaves three of the task's own exit tests permanently false.

---

## What is not blocked on this

Parts B, C and D do not depend on this question and are reported as landed in
`handoff/done/065-*.md`.

---

**This needs to be pasted to chat.** Part A cannot close — green or refused — until this is
answered.

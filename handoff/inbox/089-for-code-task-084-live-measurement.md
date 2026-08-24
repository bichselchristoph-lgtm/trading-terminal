---
id: 089
title: Complete 084's owed live measurement, now that TWS is up
type: task
class: admin
unblocks: 084's UAT (christoph/open/045) and B-138's closure
story: none
owner: claude-code
depends: 084
touches: nothing in live/ or core/ — a measurement report only
---

**Status** WRITTEN

# 089 — the number 084 owed, now that TWS is reachable

## 0. Is this task for you

**If `handoff/inbox/089-for-code-task-084-live-measurement.md` exists in
your tree and no file beginning `089-` exists in `handoff/done/`, this task
is for you. Otherwise stop reading and ignore this message.**

---

**Self-authored, admin-class**, per momentum/CLAUDE.md's rule 16 extension: no
product decision is made here, no code changes, no test changes. `084`'s own
done-note (`handoff/done/084-for-code-task-rvol-curve-cache.md`) is **already
exported to Drive** (confirmed against `MANIFEST-momentum-code-handoff.md`),
so it cannot be edited to add this measurement without creating a
tracked/Drive byte-sync divergence — the exact `040`/`043`/`052` condition
this tree's own convention refuses to create a second time (`086`'s own
triage note documents this rule in detail). **This mirrors `058` → `075`
exactly**: `058`'s own owed live measurement was completed later by a
separate task file rather than by editing `058`'s already-exported note.

## What is owed

`084`'s Part 3 recorded the live wall-time measurement — a second attach of
the same symbol against the first — as **NOT YET DONE**, because TWS was not
running at the time. TWS is now up. Run the scratch harness already written
and described in `084`'s own note (`084_cache_measure.py`, never committed),
and report the numbers here.

## Do not

Do not edit `handoff/done/084-for-code-task-rvol-curve-cache.md`. Do not
change any production file. Do not change any test.

## Prompt

```
tws is open now
```

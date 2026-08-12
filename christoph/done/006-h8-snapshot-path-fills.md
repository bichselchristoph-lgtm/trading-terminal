**Status** REVIEWED — answered by events, awaiting Christoph's confirmation
**Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Task** H8
**Done-note** `handoff/done/H8-and-corrections.md`

# 006 — Does the snapshot path fill?

---

## What it asked

H8 froze the regime snapshot path from `claude/regime-snapshots/` to `docs/regime-snapshots/`. The UAT: confirm the folder fills after the next scheduled firing, **expecting it to be empty at the time of writing.**

## What happened since

**The path is in use.** Two firings have written to it:

- `docs/regime-snapshots/2026-08-10.{md,yaml}` — the 05:00 ET read, frozen 05:16, AMBER, 8 of 11 rows, total +3
- `docs/regime-snapshots/2026-08-11.{md,yaml}` — today's read
- plus `2026-08-10-ratification.{md,yaml}`

**Observation, not inference:** the files exist and are dated. Whether their *contents* are right is a different question and was never what H8 asked.

## The check that remains, if you want it

`docs/regime-snapshots/` should contain **no file named with the old `claude/` path**, and no snapshot should be missing for a weekday the task fired. A gap would mean a firing wrote somewhere else — which is the failure H8 existed to prevent.

## What is owed

Confirm the path filled as expected. Then this closes.

**Separately, and not part of H8:** the cloud task writes these to a filesystem you cannot reach, so the `SPEC.md` §5.5a join to the trade log is unavailable and a sample cannot be reconstructed retroactively. That is an open decision, still unmade, and it loses data every day it stays open.

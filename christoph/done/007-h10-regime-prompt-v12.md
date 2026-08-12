**Status** REVIEWED — superseded, awaiting Christoph's confirmation
**Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Task** H10
**Done-note** `handoff/done/H10-regime-prompt-v1.2.md`

# 007 — Paste v1.2, and predict before you read

---

## What it asked

Paste `REGIME-PROMPT.md` v1.2 into the scheduled cloud task. **Before reading the output, write down whether you expect the reduced-card floor to fire.** The gap between prediction and result is the finding.

## Why it is superseded

**v1.2 is three revisions behind.** The cloud task now runs **v1.4**, which changed things v1.2's prediction exercise could not have anticipated:

- **v1.3** repaired the snapshot paths v1.2 still carried from the old tree — a re-supply defect the design session itself introduced — and rewrote PART E0 so the response body *is* the read.
- **v1.4** made vetoes tri-state: `fired` / `not_fired` / `undetermined`, never `false` when unevaluated.

## What was observed anyway

The floor **did** fire, on the first live firing, and it fires **every session**. Row 14 scores `null` because order-flow delta is not OHLCV-derivable, and it will keep scoring `null` until a source exists. **It does not self-resolve.**

That is why task `012` is capturing the QQQ tape today.

## What is owed

**The prediction exercise is worth keeping, against v1.4 rather than v1.2** — but as a new UAT attached to a future run, not this one.

Confirm H10's UAT is superseded and it closes.

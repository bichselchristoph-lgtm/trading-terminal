**Status** WRITTEN · **Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Task** M001
**Done-note** `handoff/done/M001-new-repo-and-adoption-gate.md`

# 004 — Count the tree before you look

---

## What this asks

**Write down how many files you think are in `D:\Dev\momentum` right now. Then run:**

```
git ls-files | wc -l
```

**The gap is the finding.** Not the number.

## Why it is still worth doing, months late

M001 built the adoption gate and then reported a near-empty tree — correct, because the gate refused everything that arrived with no origin data. That emptiness was the gate working, and it would have looked identical to the gate being broken.

**The check is calibration, not verification.** If your estimate is close, your mental model of what has entered this repo is sound and you can trust it when reviewing future adoptions. If it is far off, that gap is worth knowing before `S010` adds more.

Nothing depends on the answer. It costs thirty seconds.

## What to report

Your estimate, the actual number, and — if they differ much — which direction and what you think you were counting instead.

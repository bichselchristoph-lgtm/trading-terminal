---
id: 035
title: PDL and ATR14 are wrong in the context block
type: bug
class: product
version: 1.1
status: WRITTEN
owner: claude-code
tree: D:\Dev\momentum
---

# 035 — `PDL` and `ATR14` are wrong

**Type: bug. Class: product** — it changes a number Christoph sizes a trade from.

**v1.1 supersedes v1.0, which was never copied into the tree.** v1.0 named an off-by-one as
the likely `PDL` defect. **`034` then found a different mechanism in the same code path and
that is now the leading hypothesis.** See Part 2.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing — check this before reading further

**If `git status --porcelain` in your checkout returns empty, this task is for you.**

**If it returns anything at all, stop reading and ignore this message.** You are mid-task or
another session is writing here. Do not stage, commit, or discard what you find — see §8 of
the project instructions: another session's uncommitted work is never touched, and its author
commits it on a branch first.

---

## Worktree

**Do not work in `D:\Dev\momentum`.** That checkout is Christoph's, for merging and for running
the terminal.

```powershell
cd D:\Dev\momentum
git worktree add ..\momentum-035 -b task/035-pdl-atr14
cd ..\momentum-035
```

**Remove the worktree when the task completes** — stale ones turn `test_pytest_collection` red.

---

## Why

**`c015`'s UAT recorded both rows as wrong.** They are two of roughly five context values that
survive the scope decision of 2026-08-14 — everything chart-like moves to TradingView, and what
remains is what the stop table and the share count consume. **A wrong `ATR14` produces a wrong
3×ATR stop floor, and a wrong stop floor produces a wrong share count.**

---

## Part 0 — demonstrate the defect before fixing it

**A test never seen failing is a test whose green means nothing.**

For each value, **write the test first, run it, and record the red output** before touching the
implementation. If a value turns out to be correct — including because `034` already fixed it —
**say so and stop on that half.** Do not manufacture a fix for a defect that is not there.

---

## Part 1 — `ATR14`

### What it must be

**`atr_d14`**, per `SPEC.md` §6b.1b-ATR and `BUILD-PLAN.md` 2f:

- **Daily bars, `useRTH=True`**, stated explicitly at the fetch site
- `TR = max[(H − L), |H − C₋₁|, |L − C₋₁|]`
- **RMA-smoothed — Wilder's, α = 1/14**

**`ATR14` in the panel means `atr_d14` and nothing else.** `atr_i14` exists, is consumed by no
rule, and must not be substituted.

### The four ways this is normally wrong

1. **A simple mean of the last 14 true ranges instead of Wilder's RMA.** The most common
   implementation error in the indicator. An SMA of TR and an RMA of TR differ by several
   percent and neither looks broken.
2. **`TR = H − L` only** — dropping both gap terms. Those terms are what make ATR different from
   ADR at all; without them you have a 14-day average range wearing ATR's name.
3. **`useRTH` omitted at the fetch site.** It defaults to `True`, so this may be accidentally
   correct — **but the call site must still declare it**, and a test asserts no fetch site omits
   it. **Confirm that test actually reaches this path** rather than passing over it.
4. **Off-by-one in the bar array** — including today's incomplete daily bar, or seeding the RMA
   from the wrong index.

**Daily bars are not affected by the UTC defect below** — a daily bar has no intraday boundary
to slice. Do not assume Part 2's mechanism applies here.

### The test

Assert `atr_d14` against a **hand-computed value from a fixed bar fixture**, not against another
implementation. Include at least one bar whose gap is large enough that `H − L` and the gap
terms disagree — otherwise defect 2 passes.

---

## Part 2 — `PDL`

### What it must be

**The low of the prior regular trading session.** The level rail is RTH-based: the opening range
is a regular-session object, and PMH/PML exist precisely because pre-market needs its own pair.
**RTH only, and *prior*, not today.**

### The leading hypothesis — `034`'s finding

**`034` established that `formatDate=2` returns UTC and that `attach.py` slices `Bar.ts` by
position.** The consequence there: pre-market was computed as 04:00–05:30 ET and the opening
range as 05:30–05:35 ET. `ORH`/`ORL` read **723.82 / 723.37** against a true **726.02 / 724.03**.

**Four plausible, wrong values. No error, no flag.** `034` fixed that at the seam.

**So the first question is not "what is wrong with `PDL`" but "which session boundary does
`PDL` use, and did `034`'s fix reach it."** A prior-day boundary drawn on UTC puts the cut at
20:00 ET — so a `PDL` computed that way includes part of the prior evening and part of the
current pre-market, and is wrong by an amount that varies with the day.

**Establish this before considering the alternatives below.** If `034` already corrected the
path `PDL` reads, say so and move on.

### The other two ways this is normally wrong

1. **Off-by-one — the bar array includes today.** `bars[-1].low` is today's low. **Invisible for
   much of the session**, because both are plausible numbers. The ADR% path already excludes
   today per `BUILD-PLAN.md`; check whether the rail path reuses that exclusion or re-derives.
2. **Silent short array.** IBKR has returned 204 bars for a request of 205, no error, no flag.
   If a 2-day request returns 1, `PDL` silently becomes today's low. **Every bar request asserts
   the count it received** — confirm this one does.

### The test

**Timezone first.** A fixture whose bars span a UTC-vs-ET boundary disagreement, asserting the
prior-RTH low is taken on ET boundaries. This is the test that would have caught `034`'s defect
and it is the one most likely to go red here.

Then two fixtures for the off-by-one: one where yesterday's RTH low is **higher** than today's
so far, one where it is **lower**. The first alone lets the defect pass.

And the short-array guard: hand the fetch a deliberately short array and require
`unavailable (reason)`, **never a value derived from what arrived**.

---

## Part 3 — which rail values did `034`'s seam fix actually cover

`034` fixed `ORH`/`ORL` and touched the pre-market window that `PMH`/`PML` depend on. **It is
not established which of the remaining rail values read the corrected path and which do not.**

**Determine, for `PDH`, `PMH`, `PML` and `round`: does each derive from the boundary `034`
corrected, or from its own slicing?** Report the answer per value.

**Fix nothing here.** Anything found wrong becomes its own bug file, so the fix and its test
arrive together rather than riding along unexamined. **`PDL` is in scope only because `c015`
already reported it.**

---

## What this task does not do

**No change to which rows render.** The context block's collapse from 26 rows is `S012`.
**No touching the eight pre-existing failures** — `034`'s note places them in tasks 021–027.
No config changes, no layout changes, no new rows, no scrollbar.

---

## Last action

**Run `verify.ps1` as the final action.** Do not paste or summarise its output — the design
session reads `verify-output.txt` directly. **Do not quote a test count in the done-note.**
State that `verify.ps1` ran, and when.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with the new tests included. **Red output from Part 0 recorded in the note before the fix.** |
| **Refusal** | Claude Code | Short bar array ⇒ `PDL` renders `unavailable (reason)`, never a value from a partial fetch |
| **UAT** | Christoph | `c016` — attach a name and check `PDL` and `ATR14` against the TradingView daily chart. They must agree to the cent. |

---

## Report

In `handoff/done/035-pdl-and-atr14.md`:

- **The actual defect in each**, named precisely — or that it did not reproduce
- **Whether `PDL`'s defect was the UTC boundary**, an off-by-one, both, or neither
- The red output from Part 0, verbatim
- **Part 3's per-value answer** for `PDH`, `PMH`, `PML`, `round`
- Whether the `useRTH`-at-every-fetch-site test genuinely reaches these paths

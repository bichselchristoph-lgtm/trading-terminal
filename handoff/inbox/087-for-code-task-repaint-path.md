---
id: 087
title: The repaint path — the age that reads 0s, the flicker, and the stream that dies unmarked
type: task
class: product
story: S038
epic: 4
owner: claude-code
depends: none
touches: the repaint path, the stream lifecycle, the ATTACHED header, the HEALTH stream rows
mockup: ATTACHED mockup — the context block and its states
uat: c047
bugs:
  - id: B-140
    action: fix
  - id: B-141
    action: fix
  - id: B-143
    action: fix
---

**Status** WRITTEN

# 087 — one reading of the repaint path settles three defects

**Three rows, one mechanism, one read.** Do Part 0 before deciding anything;
each of the three carries a hypothesis and **none of them is a finding.**

---

## 0. Is this task for you

**If `handoff/inbox/087-for-code-task-repaint-path.md` exists in your tree and
no file beginning `087-` exists in `handoff/done/`, this task is for you.
Otherwise stop reading and ignore this message.**

---

## 1. What Christoph observed, verbatim

Three screens and two UAT answers, 2026-08-24.

- **The header read `0s` continuously for a long time at the start**, then later
  `stale 4994s`, `5010s`, `6014s` across twenty minutes. **Both are true.**
- **Flicker every 5–10 seconds** after switching between several symbols
  (UAT c045). **Flicker every 30 seconds or so** in a session left running
  ~100 minutes with one symbol attached.
- **`stream sector 1 updates · 6014s ago` beside `stream symbol 350 updates ·
  0s ago`**, rendered identically in HEALTH, with the sector stream dead for a
  hundred minutes.
- **`RVOL rth — (no bars today) · pending`**, still pending after those hundred
  minutes.

---

## 2. Part 0 — read, then measure, then fix

**Read the repaint path and answer these four, as read:**

1. **When is the freshness age computed?** On stream push, or on each paint from
   `now()`? **If it is computed on push, the header reads `0s` for as long as
   pushes keep arriving** — which is the healthy case, and would mean the
   instrument cannot report the thing it exists to report.
2. **How many repaint paths are there?** A 30-second interval matches nothing
   specified: the measured push cadence is a 5.002s median (008b) and the
   freshness threshold is 20s. **If values update on push and the screen
   flickers at 30s, those are two paths and one of them is unnamed.**
3. **Does `_begin_attach` actually tear the outgoing streams down**, or only
   drop its reference to them? Task 084's note says it cancels the outgoing
   symbol's streams; **that is what the code says it does, not what was
   observed.**
4. **Why does a full-screen flicker occur at all** on a framework that diffs?
   Name what forces a full redraw rather than a diff.

**Then measure, before fixing.** Flicker interval at **one, two and four
attaches**, each run recorded separately, **never averaged**. **If the interval
shortens as attach count rises, streams are accumulating. If it is fixed, it is
a timer.** One measurement decides it; no argument can. **Scratch lives in
`$env:TEMP`.**

**If Part 0 contradicts any line in §1 or §3, say so and name the line.**

---

## 3. Part 1 — the three fixes

**B-140 — the age must be computed at paint time, from `now()`.**

The whole argument for rendering an age was that **a moving number is the panel
proving its own check runs.** An age recomputed only when a push arrives is the
self-reference trap: **the freshness instrument depends on the freshness it
measures**, so it reads `0s` while healthy and only moves once something is
already dead. **A repaint must occur on a cadence that does not depend on the
streams** — otherwise a fully stalled terminal renders a confident `0s` forever.

**B-141 — one repaint per landed value, and no full-screen clear.**

Whatever Part 0 finds, the exit condition is the same: **no visible flicker at
any attach count.** If streams are accumulating, tear them down. If a second
repaint path exists, name it in the done-note and say what it is for.

**B-143 — two failures, both in what renders.**

- **HEALTH must mark a stale stream**, on the same 20-second rule the ATTACHED
  header uses. Christoph ruled that staleness reaches child panels for values
  the parent drives; **HEALTH is the panel a trader consults to find out which
  stream died, and it currently renders a dead stream identically to a live
  one.**
- **A `pending` that exceeds a bound becomes a refusal naming what did not
  arrive.** *Pending* means **nothing to report yet**; a hundred minutes of it
  is a refusal that never happened. **The bound is a threshold and therefore
  Christoph's — it is not ruled. Render the state; take the number from
  config and mark it unfitted.**

---

## 4. What you may NOT do

**Do not touch `ADR% used`.** B-142, its own task. Not this task's.

**Do not change `request_timeout_s`** — B-132, a threshold.

**Do not invent a screen state that is not in the mockup.** The stale marker
already has a ruled form; **HEALTH gets the same rule, not a new vocabulary.**
If the existing form genuinely cannot express a stale stream row, that is a
question file.

**Do not weaken anything 078, 080 or 083 built.** If a test must change shape,
say so and say why.

**Do not fix the forming-bar sawtooth.** Still ruled, still separate.

---

## 5. Exit tests

**Seen red against real pre-fix code before accepted green.**

**Green — the age advances without the streams.** Freeze every stream and
assert the rendered age **still advances across repaints**. This is the test
that would have caught B-140 and it is the most important one here: **080
shipped a green assertion that the age advances, and the live panel did not.**
Do not assert against a fixture that supplies its own clock ticks — **drive the
paint and read the rendered text.**

**Green — the age reads a real number while healthy.** With pushes arriving at
5s, the age must move through 1s, 2s, 3s, 4s. **A constant `0s` must fail.**

**Refusal — a stale stream is marked in HEALTH**, distinguishably from a live
one, at the same 20s threshold.

**Refusal — `pending` past its bound becomes a refusal** naming what did not
arrive, and is distinguishable from both a live `pending` and a value.

**Teardown — cancel-on-switch leaves nothing behind.** After N attaches, assert
the number of live subscribers is what one attach produces, not N times it.

**Fixture — B-136.** No test may read a state the shared fixture guarantees.

**Colour — unchanged.** Amber still renders only where a freshness age has
crossed its threshold, and nowhere else.

**UAT.** `christoph/open/047`. Not yours to perform or mark.

---

## 6. What the done-note must state

Part 0's four reads, as read. **The measured flicker interval at one, two and
four attaches, each separately.** Which of the two hypotheses the measurement
supports, or that it supports neither. The bound chosen for `pending`, and that
it renders unfitted. Which tests were seen red and against what.

`verify.ps1` runs as the last action. Do not paste or summarise it.

**Anything needing a decision that is not yours goes into a question file and
that session ends.**

---

## 7. The prompt

```
Do inbox 087
```

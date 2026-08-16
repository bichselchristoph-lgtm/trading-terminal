---
id: 050
title: The tape window — is 60 seconds right, should it be a print count, and is IBKR history the same stream
type: task
class: product
version: 1.2
originates: TAPE-SPEC §17.1 and §17.2 · REPLAY-SPEC §7.1
depends: 049
unblocks: the rolling-window definition in TAPE-SPEC §4, which every rolling tape reading is computed over
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 050 — the tape window

**Type: task. Class: product.** No panel work, no code change to the window. **This produces the
evidence for a product decision that is Christoph's.**

**This task originates in `TAPE-SPEC §17.1` and `§17.2`, and `REPLAY-SPEC §7.1`.** Those sections
carry the full argument — why the question is open, what would settle it, and what is already ruled
out. **Read §17.1 before starting; it contains the reasoning this file only summarises.**

**v1.2 adds the originating citation.** v1.1 added Part 3. **If more than one version exists, v1.2 is
the one to take.**

**Depends on `049`** — Part 0 inventories the corpus, Part 1 fixes the capability declaration.
**Neither is optional here.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/050-for-code-task-the-tape-window.md` exists in your tree and
`handoff/done/050-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**If `handoff/done/049-*.md` does not exist, stop.**

**Work in a worktree.** Remove it when the task completes. **Scratch in `$env:TEMP`, never the repo.**

---

## The question

**The rolling tape window is 60 seconds, stepped 5 seconds. Neither number was fitted.**

Every rolling tape reading — buyers against sellers, net, price response, the resolution word — is
computed over that window. **It is the most load-bearing unfitted constant in the tape.**

**Christoph's framing: the time-based window may be the wrong approach entirely, and the window
could be defined by a number of trades instead.**

---

## Part 1 — descriptive, time-based

Across every symbol and session available, for window lengths **10s · 30s · 60s · 120s · 300s**:

- **print count per window, distributed — not averaged.** A mean hides exactly the variation this
  task exists to measure
- **by time of day**, in half-hour buckets
- **by symbol**, with price and liquidity stated

**The window is a constant, and a constant is the defect this project keeps catching.** Thirty
seconds on a heavily-traded name is thousands of prints; on a thin name at 11:40 it may be four.
**A fixed number of seconds is simultaneously far too long for one and far too short for the
other** — which is why the settle timer was rejected and why detector windows scale with the
playbook's own range.

**Report the floor:** the window length below which the print count is too small to compute a
two-sided comparison. **Symbol-dependent, and a fact rather than a preference.**

**Report the ceiling:** at what print rate a window stops discriminating. **A metric pinned at its
ceiling is not "very fast" — it is unmeasurable at that resolution, and it saturates exactly when
the stock gets interesting.**

---

## Part 2 — count-based windows

**Compute the same distributions for the last 50 · 200 · 1000 prints**, and report **how the
wall-clock duration of a fixed-count window varies** across symbols and times of day.

**The precedent is already in the system.** The tape baseline uses a count, not a clock — twelve
completed holds against a rolling sixty. **A count is correct there for the same reason it may be
correct here: it is ready when it is ready**, and it means the same thing on a fast name and a slow
one.

**Two costs to report honestly rather than argue away.**

**The 5-second step exists so the number can be read rather than watched.** A number that changes ten
times a second cannot be read. **State what a count-based window does to the step.**

**A count-based window has no fixed memory in time.** *"Buyers 340k in the last 200 prints"* does not
say how long ago that was. **On a dead tape, 200 prints may reach back twenty minutes** — a different
claim from the one the row appears to make. **Quantify it: the 95th-percentile wall-clock reach of
each count window, per symbol.**

---

## Part 3 — measure the IBKR historical filter, before trusting any of this

**IBKR provides historical tick data via `reqHistoricalTicks`. That widens the corpus enormously and
it introduces the defect that would invalidate this whole task silently.**

**IBKR historical is filtered where the live stream is not.** This is already why the tape baseline
cannot be seeded from history: *a baseline built from filtered history and measured against
unfiltered live prints compares two bases.*

### Why it is worse for a count window than a time window

**A time window's denominator is seconds, and filtering cannot touch it.** The count inside changes;
the window does not.

**A count window's denominator IS the print count.** So filtering does not add noise to it —
**it rescales the instrument.** `last 200 prints` on a filtered stream and on an unfiltered one are
different windows wearing one name.

**And the likely filter is large.** Odd lots were **64.4% of all US equity trades in February 2025,
and 83.4% for stocks above $250.** If IBKR historical excludes them, a count window measured on
history is **wrong by a factor, not by a margin.**

### The test, and it is decisive

**Pick a symbol-day present in both `selection/phase3/ticks/` and IBKR historical.** Databento venue
data is the unfiltered reference.

Report:

- **print count, both sources, same symbol, same day, same window**
- **the ratio, and how it varies by time of day**
- **what is missing** — odd lots, off-exchange prints, condition-coded trades, or something else.
  **Name the classes, do not just report a count difference**
- **whether the ratio is stable enough to correct for, or whether it is not**

**Set `useRTH` explicitly on every call.** `reqHistoricalData` and `reqHistoricalTicks` both default
to `useRTH=True`, **and getting it wrong returns RTH-only data silently — no error, just a different
number.** A comparison that silently drops pre-market on one side would produce a ratio that is an
artefact of the parameter.

### Operational constraints on the pull, which are not optional

**Historical tick requests have their own pacing budget and a 50-simultaneous cap — separate from
the live 15-second cooldown. Do not conflate them.**

**Run it after hours.** Pacing does not relax after the close — the limit is the API's, not the
market's — but **a pull during the session would starve the attach path, or be starved by it, and
neither would report why**, because a pacing rejection looks like a slow request.

**IB Gateway restarts daily.** A long unattended pull spanning that **will be interrupted**, so the
job must be **resumable** — checkpointed per symbol-day and per tick-page — and it must **treat a
disconnection as expected rather than as a failure.** A job that cannot survive one restart is a job
that never completes, and it would fail quietly overnight where nobody is watching.

### What this part decides

**If the filter is large or unstable, IBKR historical cannot be used to fit a count-based window**,
and the window analysis must run on Databento data only. **That is a finding, not a failure.**

**If the filter is small and stable, the corpus for every future tape question just became the whole
of Christoph's trading history** at no purchase cost — **the most valuable outcome available here.**

---

## Part 4 — predictive. Only under pre-registration, and the default is not to run it

**Do not run a window sweep against forward excursion and report the best one.**

**Testing enough variants yields a winner by construction.** The best-documented order-flow signal in
the literature produces 3% out-of-sample R² and a 53% hit rate — **anything that looks materially
better is more likely an artefact than a discovery.**

**If run at all:** declare the grid before looking, in the done-note · use a holdout not looked at in
this task · state the multiple-comparison correction, **or state plainly that none was applied and
the result is therefore not evidence.**

**Parts 1–3 are the deliverable. Part 4 is optional and its absence is not a gap.**

---

## What is already settled and must not be re-derived

**Ruled out in `TAPE-SPEC §17.1`, repeated here so it is not re-proposed:**

**Do not ask "should the window be longer."** That was answered by adding the anchored window — real
absorption runs for many minutes, and the answer was **a second window rather than a longer one.**

**Do not propose collapsing the windows into one.** They answer different questions; settled.

**Do not change the window in code.** This task produces a recommendation and its evidence.

---

## Not in scope

No panel work. No code change to the window or the step. No fitting. No holdout access. No changes to
`records/tape/`. No purchasing.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export, from the main checkout** — not from a worktree.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | The window-boundary arithmetic has a test **seen red first** — an off-by-one at a window edge is the obvious defect and it would not be visible in the output. **And a test asserts `useRTH` is set explicitly at every historical call site** |
| **Refusal** | Claude Code | **A window with too few prints to compute a two-sided comparison refuses rather than reporting a one-sided one.** A symbol absent from a source produces a named refusal, never an empty distribution rendered as a flat line. **A source comparison where one side is RTH-only and the other is not refuses rather than reporting a ratio** |
| **UAT** | Christoph | `c028` — read the distributions and the filter ratio, and answer: **should the rolling window be a count of prints rather than a duration, and can IBKR history be trusted to answer that?** |

---

## Report

1. **Print-count distributions** for all five time windows, by symbol and half-hour bucket.
2. **The per-symbol floor** below which the window cannot compute.
3. **The saturation ceiling**, and at what print rate it is reached.
4. **Count-based distributions** for 50, 200 and 1000 prints, with **the 95th-percentile wall-clock
   reach of each.**
5. **The IBKR-versus-Databento print ratio**, by time of day, **and what classes of print are
   missing.**
6. **Whether the filter is stable enough to correct for.**
7. **Which unit is more stable across the corpus**, with the numbers that say so.
8. **What a count-based window does to the 5-second step.**
9. **Whether Part 4 was run**, and if so its pre-registration.
10. **What you could not do**, and why. Empty is suspicious.

---

## The questions this task hands back to Christoph

**Should the rolling window be a count of prints rather than a duration?** It changes what he reads
on screen, so the decision is his. **This task's job is to make sure he decides against numbers
rather than against an argument.**

**And can IBKR historical ticks be used as the research corpus?** If yes, every future tape question
gets the whole of his own trading history for free. **If no, that is worth knowing before a window is
chosen on data that does not describe the live stream.**

**Both answers land back in `TAPE-SPEC §17.1` and `§17.2`, which is where the next slice will
originate.**

---
id: 049
title: Validate what is already owned, before buying any more data
type: task
class: product
version: 1.3
originates: TAPE-SPEC §17.3 · REPLAY-SPEC §7.2
depends: none
unblocks: the Databento purchase decision, task 050, and whether E1 (sweep) and M2 (depth reliability) are ever allowed to render
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 049 — validate the owned corpus

**Type: task. Class: product.** No panel work. **This decides whether two tape components are permitted
to render at all**, which is why it is product rather than research.

**This task originates in `TAPE-SPEC §17.3` and `REPLAY-SPEC §7.2`.** Those sections carry the
argument — why it is open, what would settle it, and what is already ruled out. **If anything in this
file appears arbitrary, the reasoning is there and not lost.**

**v1.3 adds the originating citation.** v1.2 removed Part 4 to task `050`; v1.1 briefly carried it.
**If more than one version of this file exists, v1.3 is the one to take.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/049-for-code-task-validate-the-owned-corpus.md` exists in your tree and
`handoff/done/049-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes. Do not remove another session's.

**Scratch goes in `$env:TEMP`, never in the repo.**

---

## Why this exists

**Five venues, 245 dates, 999 files are already on disk and have never been used.** The design
session has twice recommended purchasing more Databento data before the owned corpus was touched.

**That is the expensive version of the same step**, and this task is the cheap one.

**Two questions are answerable today at zero marginal cost:**

1. **Does the sweep component (E1) survive contact with real multi-venue data?**
2. **Does the depth-reliability component (M2) pass its own falsification test?**

**A negative answer on either is a good outcome and ends work on that component.**

---

## Part 0 — inventory, and stop if the record is wrong

**Report what is actually on disk before doing anything with it.**

For `selection/phase3/ticks/`:

- file count, total size, date range
- **which venues** are present, by filename and by `publisher_id` in the data
- **which symbols** are present — the record claims five venues over 245 dates but **does not say
  which tickers**
- **which record types** — `trades_` is confirmed; `imbalance_` is claimed for four venues;
  **whether any order-level or depth data exists at all is unknown**
- whether **SPY** is present, and in which record types
- **the price and liquidity spread of the symbols present.** Not needed by this task —
  **`050` needs both a heavily-traded name and a thin one, and whether the corpus contains both is
  unknown.** Collect it here because the inventory is being read anyway.

For `records/tape/`:

- session count, date, symbol, record counts by type

**If the corpus is materially different from the above, report it and stop.** Do not proceed on a
guess about what the data contains. **The whole point of this task is that the owned data is
unexamined, so the inventory is a real deliverable and not a preamble.**

---

## Part 1 — the capability declaration defect

**`DatabentoReplayFeed.capabilities` is a class attribute without `MULTI_VENUE`, while `IBKRFeed`
sets `self.capabilities` per instance.**

**Consequence: the replay adapter cannot report multi-venue even when replaying a merged slice.**
That defect was once read as a vendor limitation and a component was killed for it wrongly.

**Fix: derive capability from the data, not from the class.** A `publisher_id` count over the slice
being replayed determines whether `MULTI_VENUE` is present.

**A test must go red on the old behaviour first.** Construct a merged slice from two venues, assert
the adapter reports `MULTI_VENUE`, and confirm the assertion fails against the class-attribute
version before the fix.

**This part blocks Part 2, and it blocks `050`.** Do it first.

---

## Part 2 — sweep / ISO validation (E1)

**Merge the venue streams on `ts_recv`, never on `ts_event`.**

**`ts_event` is a subtle lookahead.** Venue matching-engine clocks differ; `ts_recv` is the capture
time, PTP/GPS-synced and monotonic per symbol. **A merge on `ts_event` produces a result that looks
correct and is not.** A test should assert the merge key.

**Declare the construction and carry it as the value's basis.** A sweep is *N prints across M venues
inside a T-microsecond window, same direction, consuming multiple levels.* **N, M and T are
parameters and none of them has a fitted value** — pick starting values, state them, and render the
result as `unfitted`.

**The ISO flag is not needed and its absence is not a gap.** A direct venue feed carries no
condition column because the venue's message *type* is the condition. **With five venue streams
merged you observe the sweep directly rather than inferring it from a flag** — which is a stronger
construction than the published work used, not a weaker one.

**What to produce:**

- sweep count per session, per symbol, per side
- **the distribution of N, M and T across detected sweeps** — this is what makes the parameters
  fittable later rather than guessed forever
- **forward excursion after each sweep** at horizons that match a decision cycle, not a tick

**Do not fit anything.** This part establishes that the component *measures* something. Whether it
*predicts* anything is a separate question requiring a declared holdout, and **the holdout must not
be looked at in this task.**

---

## Part 3 — the SPY falsification test (M2)

**Conditional on Part 0.** M2 needs order-level or depth data. **If the corpus holds only trades and
imbalance, this part cannot run — report that and stop on this part only.** Part 2's result still
stands.

**If the data exists:**

**Over 99.75% of SPY orders are cancelled before trading, attributed entirely to legitimate ETP
arbitrage repricing.** Run the depth-reliability measurement on SPY.

- **If arbitrage repricing dominates the output — the component is behaving correctly.** That is the
  expected result and it is a pass.
- **If it does not dominate — the implementation is broken.** That is the finding, and it is worth
  more than a positive result would be.

**Do not use the QQQ ARCA capture for this part.** ARCA depth rows arrive out of price order
(`018` part 1, unfixed), which makes every book-derived measure wrong *silently*. **This part uses
Databento data only.**

---

## Not in scope

**No purchasing.** No terminal work, no panel work, no rendering. **No fitting and no holdout
access.** No changes to `records/tape/` — the tape is intact and is never touched; if a read is
wrong, the read path is wrong.

**No absorption harness.** Separate task. **No window analysis.** That is `050`.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export, from the main checkout** — not from a worktree.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | The `MULTI_VENUE` derivation test and the `ts_recv` merge-key test both **seen red first**, then green |
| **Refusal** | Claude Code | A slice from a single venue reports **no** `MULTI_VENUE` — the capability must be derived, not assumed present now that it is derived at all. And a corpus missing a required record type produces a named refusal, never an empty result set |
| **UAT** | Christoph | `c027` — read the inventory and the sweep distribution and answer one question: **is this enough to decide what to buy?** |

---

## Report

1. **The Part 0 inventory, in full.** Venues, symbols, date range, record types, sizes, and the
   price/liquidity spread of the symbols present.
2. **Whether SPY is present**, and in which record types.
3. **What the capability declaration did before and after**, with both reds quoted.
4. **The sweep counts and the N / M / T distributions.**
5. **Whether Part 3 could run**, and if not, exactly what is missing.
6. **Whether `050` can run on this corpus** — specifically, whether it contains both a
   heavily-traded name and a thin one.
7. **What you could not do**, and why. Empty is suspicious.

---

## The question this task hands back to Christoph

**How many observations, per component, on how many distinct names, before a threshold may leave
`unfitted`?**

**A gate with no number is not a gate**, and the Databento purchase cannot be sized without it.
Report the counts Part 2 produced so the question can be answered against real numbers rather than
in the abstract. **The argument sits in `TAPE-SPEC §17.4`.**

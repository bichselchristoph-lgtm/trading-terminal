---
task: 070
class: product
story: S034 S035 S037
epic: 4
depends: none
touches: the ADR statistic, the ATTACHED renderer, the panel snapshot fixtures
---

# 070 — the context block, built from the mockup

**If `handoff/inbox/070-for-code-task-attached-context-block.md` exists in your tree and `handoff/done/070-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. The mockup is the specification

**`ATTACHED mockup — the context block and its states`, v1.0, in the Drive `Mockups/` folder.** ATTACHED-SPEC v1.5 carries the reasoning; **the mockup carries what renders, and where a word differs the mockup wins on layout and the spec wins on meaning.**

**Ruled by Christoph 2026-08-23, and none of it is open:**

- **The context block carries `ADR% used`.**
- **No ATR in this panel. TRADE's stop selector is its only surface in the whole terminal.**
- **No other ADR metric.** No `ADR$`, no `ADR%avail`, no room up, no room down.
- **`ATR14` and `ADR14` are invalid everywhere** — label, key, value or spec statement.

**Do not re-open any of these, and do not ask for confirmation of them.** If something in the tree contradicts them, the tree is what changes.

---

## 1. Part 0 — the inventory and the file map, before anything else

**Read the panel's current render path and report, as a list:**

1. **Every row the context block renders today**, by label.
2. **Whether an ATR row is among them.** §3 of the spec says there should be none; `B-091`'s repro reads one. **One of those is wrong and this establishes which.**
3. **Whether `ADR$` or any room value still reaches the renderer.** `B-028` records the ADR dollar value continuing to arrive after its row was deleted.
4. **The file set each part below must write.**

**Report it even where nothing is wrong.** The inventory is the finding this task most needs to produce, because two documents currently disagree about what is on screen.

---

## 2. Part 1 — the fixtures come first and must be seen red

**`PROCESS §9`: the mock is agreed, the snapshot test is written from the mock, it is run and it is RED, and only then is the panel built until it is green.** **Step 3 is the one that gets skipped and it is the one that matters** — `test_no_secrets.py` went green on both occasions a live key sat in a committed file.

**Write a snapshot fixture for each of the five states in the mockup:**

| | State | Mockup § |
|---|---|---|
| 1 | Attached and landed | §1 |
| 2 | Attaching — one screen-level badge | §3 |
| 3 | Nothing attached | §4 |
| 4 | Partial gather — `N of M rows unavailable` | §5 |
| 5 | Re-attach inside the cooldown — `queued · 11s` | §6 |

**All five at 209 × 54**, which is the size the terminal actually runs at and which the snapshot suite does not currently pin — `B-012`. **Do not widen the suite's other widths and do not remove them.**

**Ambiguous-width characters are counted.** `B-010`: box widths of 69–71 against a 71-character border were invisible in HTML and visibly broken in the console.

**Run them before building anything. Report which were red and which were already green.** **A fixture that is green before the work starts is a fixture that is not testing the change** — say so rather than accepting it.

---

## 3. Part 2 — `ADR% used`

**The row renders `ADR% used`, a percentage, with the bar.**

```
  ADR% used   64%  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░
```

**The arithmetic is the complement of what the code already computes.** `ADR%avail` was `36%` and `ADR% used` is `64%`. **Use the existing `ADR%avail` computation and render `100 − avail`** rather than writing a second formula — two formulas for one quantity is how `atr_d14` and `atr_i14` happened.

**Underlying, for the record:** the share of a typical day's range that today has already consumed — today's high minus today's low, over `ADR20` expressed in dollars.

**It can exceed 100%.** A day whose range is larger than the 20-session average is ordinary. **The bar clamps at full; the number does not.** A value silently capped at 100 would answer a different question.

**`ADR20` unavailable ⇒ the row reads `unavailable` with its reason.** Never a blank, never zero.

**The row carries what it was computed over**, per the standing rule that every value renders its basis. **`ADR20` is RTH, 09:30–16:00 ET.**

---

## 4. Part 3 — the removals, and the leak check

**Remove from the panel:** `ADR$` · `ADR%avail` · `room up` · `room down` · **any ATR row**.

**Removing the row is half of it.** `B-028` records the ADR dollar value still reaching the renderer after its row was deleted — **a field that does not exist cannot be rendered by accident, and a field that still arrives can.**

**So: remove the row, and remove the value from the record the renderer reads.** **A test asserts the field is absent from that structure**, not merely unrendered.

**If Part 0 found an ATR row in the context block, it is the same shape** and gets the same treatment. **If Part 0 found none, say so and change nothing** — and the spec was already right.

---

## 5. Part 4 — the four non-landed states

**058 built the worker, the atomic swap and the badge. This part verifies them against the mockup rather than rebuilding them.**

- **Attaching** — one screen-level badge, old values dropped immediately, **no row fills independently**, everything lands in one paint.
- **Nothing attached** — `not attached`, one row.
- **Partial gather** — `N of M rows unavailable`. **Never a partial context.**
- **Cooldown** — `queued · 11s`. **Never a silent drop.**

**Where the built behaviour and the mockup differ, the mockup is the specification and the code changes.** **Report every difference you found, including the ones you fixed** — that list is what tells the design session whether 058's drawing was ever right.

---

## 6. Parallelism

**Parts 2, 3 and 4 run as subagents only if Part 0 shows their file sets are disjoint.** They plausibly share one renderer, in which case **they serialise in the order 3 → 2 → 4**: remove first, so the new row is added to a clean set.

**Part 1 precedes all of them and is not parallel with anything.** That is the whole point of writing the fixture first.

**No subagent commits. The parent commits once.** A convention, not a control.

---

## 7. Not in this task

- **The TRADE stop table and its ATR20 selector.** Its own mockup exists; its own task will.
- **`B-076`**, the ATR multiplier. A threshold, so Christoph's.
- **`B-005` / `B-011`** — the truncated basis tail and the too-small guard. Related, separately scoped. **If the `ADR% used` row's basis tail is cut on screen, report it and do not widen the guard from here.**
- **The level rail.** That is `067`.
- **`UI mockup — core surface panels`**, which still draws `ADR%avail`. The design session owns retiring it.

---

## 8. Exit tests

**Green.**
- **Five snapshot fixtures at 209 × 54, each seen red before the build**, or reported as already green with the reason.
- **`ADR% used` renders as a percentage with its bar and its basis**, computed as the complement of the existing value.
- **A day whose range exceeds `ADR20` renders above 100% with the bar clamped.**
- **No ATR anywhere in this panel.** No `ADR$`, no `ADR%avail`, no room values.
- **A test asserts the removed fields are absent from the record the renderer reads**, not merely unrendered.
- **The four non-landed states match the mockup.**

**Refusal.**
- **`ADR20` unavailable** ⇒ the row reads `unavailable` with its reason and every other row still renders.
- **Partial gather** ⇒ `N of M rows unavailable`, never a partial context.
- **Splice unverified** ⇒ `VWAP unavailable (splice unverified)`.
- **No sector mapping** ⇒ `RVOL_rel unavailable (no sector mapping)`, never 1.0.

**UAT (Christoph).** `christoph/open/038-*`.

---

## 9. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**Two things belong in the done-note that are not code:** **Part 0's inventory**, and **every difference found between 058's built behaviour and the mockup.** Both are facts about the screen that no document currently states correctly.

---

**This note needs to be pasted to chat.**

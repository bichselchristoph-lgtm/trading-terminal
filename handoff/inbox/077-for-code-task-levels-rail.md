---
task: 077
class: product
story: S033
epic: 5
supersedes: 074
depends: none
touches: the session module, the levels computation, a new LEVELS panel
---

# 077 — the LEVELS rail: eleven built, thirteen unbuilt, one unspecified

**If `handoff/inbox/077-for-code-task-levels-rail.md` exists in your tree and `handoff/done/077-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Supersedes 074, which superseded 067

**067 carried a reconstruction of which levels were built. It was wrong, and 071 read the code and established the truth.** The count was right and the membership was wrong — **which is worse, because a count that matches looks confirmed.** 067 named `PMH` and `PML` among the unbuilt and `HOD` and `LOD` among the built. **It is the other way round.**

**074 was correct on that and cited task `073`, which is now retired.** Christoph ruled 2026-08-23 that converting an already-built panel to row descriptors was not worth a session — **the panels are mostly static, and the payoff was speculative.** **The pattern moves here instead, where it costs nothing**: this task builds a panel from scratch, and building it declaratively is free where converting one is not.

---

## 1. What exists today, read from the code by 071

**`RAIL_ORDER` and `Attached.rail` carry eleven rows, populated on every attach:**

```
PDH  PDL  PMH  PML  ORH5  ORL5  ORH15  ORL15  52wH  52wL  round
```

**071 stopped rendering them in ATTACHED and deliberately left them on the record.** **So the data is computed right now and reaches no screen at all.** That gap is live, and closing it is the first half of this task.

**Ten of the eleven are levels LEVELS-SPEC names. `round` is not one of the twenty-three** — §4.

**Thirteen of the twenty-three are unbuilt:**

```
HOD  LOD  ·  PDO  PDC  ·  PWH  PWO  PWL  PWC  ·  MoMH  MoMO  MoML  MoMC  ·  ATH
```

**`HOD` and `LOD` being absent is worth pausing on.** They are the high and low of the current session — **the two most-consulted intraday levels, and the cheapest to compute from data already in hand.** Report why they are missing if the reason is visible; do not guess.

---

## 2. Part 0 — confirm the inventory, then map the files

**071's reading is a task's report, not a measurement you made.** Confirm it:

1. **List `RAIL_ORDER` and every key `Attached.rail` carries after a live attach.** Eleven, or something else.
2. **Is `round` computed from a parameter?** LEVELS §6 permits only definitions with no free parameters. **A rounding increment is a parameter.**
3. **Are `HOD` and `LOD` computed anywhere** — in the record, in the session module, at all?
4. **The file set for the new panel.** `073` is retired; there is no descriptor to build on and none to collide with.

---

## 3. Part A — the session module comes first

**`B-043`. `marketstate.py` builds its own Session from config strings with no holidays and treats half-days as full days — `rth_close` lands at 16:00 on a day the market shut at 13:00.**

**This is a precondition, not a neighbour.** **Every level below is a window extreme**, and a prior week containing a half-day computes its high from bars that were never traded. **Thirteen new levels on a broken session module is thirteen new plausible wrong numbers.**

**Required:** one session module, not two · holidays and half-days, with a half-day test seen red first · **every boundary computed from a timezone-aware timestamp in US/Eastern via `zoneinfo`, never from an index into an array** — B-023, and `attach.py` has been wrong here before.

---

## 4. `round` is rendering and the spec does not name it

**LEVELS-SPEC lists twenty-three levels. `round` is not among them.** ATTACHED's disposition table expects it to survive as a level in the rail, so one document expects it and the owning document does not define it.

**Do not delete it and do not render it. Report what it computes and from what parameter.** **If it takes an increment — 0.50, 1.00, whatever — it is a detection, not a definition**, and LEVELS §6 rules those out: every method has parameters, and the moment they are tuned the terminal is deciding what Christoph trades.

**The ruling is the design session's. This task establishes the fact.**

---

## 5. Parts B–E — the thirteen windows

| Part | Window | Levels |
|---|---|---|
| **B** | Today | `HOD` `LOD` |
| **C** | Prior day | `PDO` `PDC` |
| **D** | Prior week | `PWH` `PWO` `PWL` `PWC` |
| **E** | Prior month | `MoMH` `MoMO` `MoML` `MoMC` |

**All depend on Part A. Parallel between themselves only if Part 0's file map says the sets are disjoint** — if they share one module they serialise. **Do not force parallelism onto a collision.**

### Composition is the test, and it is stronger than any fixture

**`PWH` must be the maximum of that week's `PDH`s. `MoMH` must be the maximum of that month's.** **Assert it per level, against real bars.**

**That is what makes the rail one structure rather than a list of separately-computed numbers.** A level failing composition renders a plausible price at a plausible level and nothing looks broken.

**Every level is RTH.** The stated cost: these will not match an ETH TradingView chart, and the terminal says which basis it used.

### ATH may not fit the request budget

**058 collapsed the daily fetches into one 1Y request, and a year of bars cannot produce an all-time high.** **ATTACHED §3 allows three requests per attach and rules out any cache.**

**Do not add a fourth request on your own authority and do not widen the 1Y one silently.** **Write a question file naming what ATH would cost in requests and duration, and continue with the rest.**

---

## 6. Part F — the panel, built from a row list

**Build it from `LEVELS mockup — the rail against the running terminal`, v1.4, in the Drive `Mockups/` folder. The mockup outranks the spec on layout** — B-122.

```
+- LEVELS ------------------------------------------------ 23 of 23 +
  ▲ above   HOD · ORH15 ORL15 · PWH · MoMC MoMH · ATH · 52wH · 52wL
  next      HOD  $733.39   +$0.25
            ──────────────────  price  $733.14  ──────────────────
  next      PWC  $731.05   −$2.09
  ▼ below   PMH PML · ORH5 ORL5 · LOD · PDL PDO PDC* PDH · PWL PWO PWC · MoML MoMO
  * PDC $726.80 gapped over — no trade there today          l = add a level
  6 of 6 · end
```

- **`above` holds levels above price, `below` holds levels below, price renders between them.** The label describes price, never the trader — side is declared in TRADE.
- **`next` is the nearest level on each side**: level, price, signed distance **in dollars**.
- **No ADR anywhere on the panel. No `clear for`.** Both deleted 2026-08-23.
- **The caption is the true count of the true total** — `23 of 23`, `17 of 23`.
- **Left to right is most recent to most durable**, not nearest to furthest.

### Build the rows as a list, because this panel is new

**Each row is one entry carrying its key, its label, how its value becomes a string, and what renders when it is absent.** **The panel renders the list; it does not know the rows individually.**

**This is not a refactor and it is not a framework.** It is how a new panel is written when the alternative costs nothing. **Do not generalise it, do not extract it into shared machinery, and do not touch any other panel** — `073` proposed exactly that and was retired for it.

**Resolved at import, immutable after.** **No runtime toggle and no config file for rows.** Christoph, 2026-08-23: *"Any information added or removed is at config time. The only exception is attaching to a symbol."* **A row that can be turned off at runtime is a refusal that can be turned off at runtime.**

**One test carries the value: a level absent from the list is absent from the record the renderer reads.** **That is `B-028` made impossible rather than caught** — the ADR dollar value kept arriving after its row was deleted.

### Fixtures first, and assertions that can fail

**Write the snapshot fixtures from the mockup before the panel, and see them red.** PROCESS §9, and **the step that gets skipped is step 3.** `070` and `071` both wrote fixtures after the code and both said so. **This is the one that stops the streak.**

**And write assertions that can fail.** `071` found that `"ATTACHING" in body` passed on two different wordings, so `070`'s claim of a match was never tested. **An assertion loose enough to pass on the wrong output has not tested anything.**

---

## 7. Not in this task

- **The eight other rail states.** B-078, the design session's to draw.
- **`B-076`**, the ATR multiplier. Christoph's.
- **`B-112`'s label question.** Settled — Option A is in the mockup.
- **Deleting `round`, or rendering it.** §4.
- **ATTACHED.** `071` landed; do not re-enter that panel.
- **Any other panel's row structure.** §6.

---

## 8. Exit tests

**Green.**
- **Part 0's confirmed inventory is in the done-note**, including what `round` computes from and whether `HOD`/`LOD` exist anywhere.
- **One session module, half-days and holidays handled, half-day test seen red first.**
- **Every unbuilt window now computes**, except any blocked by §5's ATH question and named there.
- **Composition asserted** — `PWH` equals the max of that week's `PDH`s.
- **The LEVELS panel renders**, matching the mockup, with fixtures **written first and seen red**.
- **A level removed from the row list is absent from the record**, asserted by test.

**Refusal.**
- **A window unresolvable in ET** ⇒ every level from it absent with its reason. **Never a boundary drawn by bar position as a fallback.**
- **A session incomplete** ⇒ absent with its reason, **never a partial extreme.**
- **`N of 23` and a full rail are visibly different.**
- **Nothing attached** ⇒ `not attached`, and no price row.

**UAT (Christoph).**
- **One name per window where the extreme printed outside regular hours.** **An RTH high can never exceed the ETH high; an RTH low can never sit below the ETH low.** A value on the wrong side is a defect; equality proves nothing. B-093.
- **One half-day, checked deliberately.**

---

## 9. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note carries the confirmed inventory and the `round` finding.** Both are facts about the tree that no document currently states correctly, and the last two attempts to state them from outside the code were wrong.

---

**This note needs to be pasted to chat.**

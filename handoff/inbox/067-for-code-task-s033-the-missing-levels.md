---
task: 067
class: product
story: S033
epic: 5
depends: none
answers: handoff/questions/065-levels-panel-scope.md
touches: the session module, the levels module, the rail renderer
---

# 067 — S033: build the levels the rail does not have

**If `handoff/inbox/067-for-code-task-s033-the-missing-levels.md` exists in your tree and `handoff/done/067-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. This answers your question file, and the answer is that the task was wrong

**`065` Part A said "render the three levels into the existing rail structure and change nothing else" and then set an exit test requiring twenty-three.** You were right to stop rather than pick a half.

**The scope line was written on an assumption nobody checked: that the tree already had twenty levels.** It has ten. **A count read from an artifact is a count as of that artifact's world**, and the design session read LEVELS-SPEC and treated it as a description of the code. It is a specification of the product.

**LEVELS-SPEC wins.** It is authoritative for product behaviour and the twenty-three ruling is closed. **So the exit test was right and the scope line was wrong.** Build the missing levels.

**And `B-017` was a misdiagnosis.** It said 52wL was ruled but absent. **It renders, and so do ORL5 and ORL15.** The real gap was never three restored levels.

---

## 1. Part 0 — the inventory, before anything else

**Do not start from the design session's arithmetic. Read the tree.**

**Report, as a list: which of the twenty-three levels the code computes today, and which it does not.**

**One reconstruction, offered as a hypothesis to confirm or destroy, not as a finding.** Ten existing would fit `HOD LOD ORH5 ORH15 ORL5 ORL15 PDH PDL 52wH 52wL`, leaving thirteen: `PDO PDC PMH PML PWH PWO PWL PWC MoMH MoMO MoML MoMC ATH`. **That is arithmetically consistent and it may be wrong.**

**It is probably wrong in at least one place, and here is the contradiction to resolve first.** **LEVELS §9.1 records that Christoph's UAT on 2026-08-22 confirmed 52wH, 52wL and ATH are correctly anchored to RTH and rendered.** If ATH renders, the reconstruction above is wrong and the missing count is not thirteen. **Say which is true. Do not reconcile it by picking the one that makes the arithmetic work.**

**The inventory is the finding this task most needs to produce.** Everything below is scoped by it.

---

## 2. Part A — the session module, and it comes first

**`B-043`. `marketstate.py` builds its own Session from config strings with no holidays and treats half-days as full days — `rth_close` lands at 16:00 on a day the market shut at 13:00.**

**This is a precondition, not a neighbour.** **Every level below is a window extreme**, and a prior week containing a half-day computes its high from bars that were never traded. **Thirteen new levels on a broken session module is thirteen new wrong numbers, each one plausible.**

**Required:**
- **One session module.** Not two. The session is currently built twice.
- **Holidays and half-days.** A half-day test that would have caught this.
- **Every boundary computed from a timezone-aware timestamp in US/Eastern via `zoneinfo`.** **An index into an array is never a session boundary** — B-023, and `attach.py` has been wrong here before, with `formatDate=2` returning UTC and `Bar.ts` sliced positionally.

**Nothing in Parts B–E starts until Part A lands.** That is a real dependency and forcing it into parallel would produce work built on the thing being replaced.

---

## 3. Parts B–E — the windows

**Partition by window. Each is independent of the others and all depend on Part A.**

| Part | Window | Levels |
|---|---|---|
| **B** | Prior day, completion | `PDO` `PDC` |
| **C** | Pre-market | `PMH` `PML` |
| **D** | Prior week | `PWH` `PWO` `PWL` `PWC` |
| **E** | Prior month | `MoMH` `MoMO` `MoML` `MoMC` |

**Scoped by Part 0's inventory** — a window already built is reported and skipped, not rebuilt.

**Run as parallel subagents only if Part 0 shows their file sets are disjoint.** **If they share one levels module, they serialise. Do not force parallelism onto a collision** — an asserted partition is how two agents overwrite each other.

### **Composition is the test, and it is stronger than any fixture**

**`PWH` must be the maximum of that week's `PDH`s. `MoMH` must be the maximum of that month's.** **Assert it, per level, against real bars.**

**That is what makes the rail one structure rather than a list of separately-computed numbers.** A level that fails composition is wrong in a way no eyeball catches — **it renders a plausible price at a plausible level and nothing looks broken.**

**Every level is RTH.** Task 041, LEVELS §1. **The accepted cost is stated in the spec: these will not match an ETH TradingView chart, and the terminal says which basis it used.**

---

## 4. ATH is the one that may not fit, and that is a decision

**`058` collapsed the daily fetches into one 1Y request. A 1Y series cannot produce an all-time high.**

**If ATH is not already built, it needs either a longer request or a source this task does not have.** **ATTACHED §3 allows three requests per attach and rules out any cache or local store** — *"if this panel ever needs a cache, the no-database decision was wrong."*

**Do not add a fourth request on your own authority, and do not quietly widen the 1Y one without saying so.** **Write a question file naming what ATH would cost in requests and duration, and continue with the rest.** If Part 0 finds ATH already renders, say what it is computed from — **that answer is itself the finding.**

---

## 5. Part F — the caption, not the layout

**Build:** the caption reads `23 of 23`, and `N of 23` when levels are absent. **Each absent level carries its reason.**

**Do not build:** the four-line rail at twenty-three tokens. **There is no current mockup at that count** — LEVELS §9.2 names it as the one thing that has physically changed — and PROCESS §9 requires the mock agreed and the snapshot written from it before the panel. **The redrawn mock is the design session's and it is not done.**

**So this task delivers computation and the caption arithmetic.** The rail layout follows the mock.

**`Nothing more here` and `more below` must not render identically.** That distinction is the whole refusal and it is testable today, without the mock.

---

## 6. Not in this task

- **`B-112`**, the `above` and `below` rows listing levels on the opposite side to their labels. A spec defect, the design session's.
- **`B-078`**, the eight rail state mocks and the twenty-three-token rail. Also the design session's.
- **`B-093`**, RTH anchoring unverified for twenty of twenty-three. **Verification is Christoph's, and it gets easier once the levels exist** — one name per window, six checks, not twenty-three.
- **Anything in `tws_order`.** That is `066`.
- **`065`'s Parts B, C and D.** Done or confirmed already correct.

---

## 7. Exit tests

**Green.**
- **Part 0's inventory is in the done-note as a list**, and it states whether ATH renders.
- **One session module, holidays and half-days handled, with a half-day test seen red first.**
- **Every level Part 0 found missing now computes**, except any blocked by §4 and named there.
- **Composition asserted: `PWH` equals the max of that week's `PDH`s, `MoMH` the max of that month's.**
- **The caption reads the true count of the true total.**

**Refusal.**
- **A window that cannot be resolved in ET** makes every level from it absent with its reason — **never a boundary drawn by bar position as a fallback.**
- **A session incomplete** renders the level absent with its reason, **never a partial extreme.**
- **`N of 23` and a full rail are visibly different.**
- **A missing ATH renders absent with its reason**, never omitted silently.

**UAT (Christoph).**
- **One name per window where the extreme printed outside regular hours.** **An RTH high can never exceed the ETH high; an RTH low can never sit below the ETH low.** A terminal value on the wrong side of the chart's is a defect and equality proves nothing.
- **One half-day, checked deliberately.**

---

## 8. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**Two things belong in the done-note that are not code:** **the Part 0 inventory**, and **whether §9.1's ATH claim held.** Both are facts about the tree that no document currently states correctly, and this is the run that establishes them.

---

**This note needs to be pasted to chat.**

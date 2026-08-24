---
task: 090
class: product
story: S033
epic: 5
supersedes: 077
depends: none
touches: the level rail's prior-day selection, a new LEVELS panel and its caption, the app's panel set
---

# 090 — the LEVELS panel: render the ten that already compute, against mockup v1.5

**If `handoff/inbox/090-for-code-task-levels-panel.md` exists in your tree and `handoff/done/090-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. This supersedes 077, and the reason is the mockup moved

**077 cites `LEVELS mockup — the rail against the running terminal` v1.4 and reproduces its layout in its §6. v1.4 is now `- OLD`.** The current file is **v1.5**, `LEVELS mockup — the rail against the running terminal - LATEST`, in the Drive `Mockups/` folder, ruled by Christoph 2026-08-23 with four amendments.

**v1.5 is not a redraw of v1.4. It replaces the panel's selection mechanism.** The token strips and the single `next` row are gone; the rail now windows to one ADR either side of price and truncates at five per side. **Building 077 as written would build a panel Christoph has already ruled against.** That is the whole reason this file exists.

**077 also ordered the work session-module-first, then thirteen new windows, then the panel — several sessions before anything reaches a screen.** This task inverts that for one stated reason, in §1.

**The thirteen unbuilt windows and the session module (`B-043`) are not dropped. They are a separate, later task**, and this file's §7 says what it is leaving to it.

**`067` and `074` were already superseded by `077` and remain so.** `NOW.md` currently lists `h067` as *ready* — it is not; the supersession chain `067 → 074 → 077 → 090` is stated here so a session reading `NOW.md` alone does not pick it up. **Do not act on `067`, `074` or `077`.**

**One earlier draft of this file exists in `Superseded tasks/` as `090-for-code-task-levels-panel v1 - OLD.md`.** It lacks §4's caption finding and nothing else. It never reached a tree. **Nothing was deleted to replace it.**

---

## 1. Why the panel comes before the session module, said plainly

**Ten of the twenty-three levels compute on every attach right now and reach no screen at all.** `071` stopped rendering the rail inside ATTACHED and left the data on the record. That gap is live today, and it is the whole of what this task closes.

**077 §3 made the session module a precondition on the grounds that "every level below is a window extreme".** That argument is correct **for the thirteen unbuilt windows** — prior week, prior month, and anything spanning a half-day. **It does not obviously bind the ten that already compute**, because `B-043`'s defect is that `rth_close` lands at 16:00 on a 13:00 day, and none of the ten reads `rth_close`: `PMH`/`PML` slice before `09:30`, `ORH5`/`ORL5`/`ORH15`/`ORL15` slice from `09:30`, `PDH`/`PDL` come from `useRTH=True` daily bars, `52wH`/`52wL` are extremes over the whole `rth_dailies` series.

**That is a claim this session made by reading, and it is exactly the kind of claim this project has been wrong about before.** **Part 0 confirms or destroys it. Do not accept it.** If any of the ten does read a session boundary this reasoning missed, **say so and stop before §3** — that finding is worth more than the panel.

**`B-043` stays open either way.** It is not fixed here and it is not closed here.

---

## 2. Part 0 — confirm the inventory, from the code

**077 §2 asked for this and it has never been produced.** `067` produced a reconstruction that was wrong in membership while right in count — **which is worse, because a count that matches looks confirmed.**

Report, as a list, read from the tree and not from any document:

1. **`RAIL_ORDER` and every key `Attached.rail` actually carries after a live attach.** Eleven, or something else. This session read `live/tui/app.py:476` as `PDH PDL PMH PML ORH5 ORL5 ORH15 ORL15 52wH 52wL round` — **confirm it against a live attach, not against that line.**
2. **Which of LEVELS-SPEC's twenty-three each of those keys is**, and which of the twenty-three has no key at all.
3. **`067` §1 records that LEVELS §9.1 claims Christoph's 2026-08-22 UAT confirmed `ATH` renders.** `core/indicators/context.py`'s `level_rail` has no `ATH` parameter. **Say which is true. Do not reconcile it by picking the one that makes the arithmetic work.**
4. **`round` — what it computes and from what parameter.** 077 §4's ruling is unchanged and carries forward verbatim: **do not delete it and do not render it.** If it takes an increment — 0.50, 1.00, whatever — **it is a detection, not a definition**, and LEVELS §6 rules those out. **This task establishes the fact; the ruling is the design session's.**
5. **Whether any of the ten reads a session boundary `B-043` gets wrong** — §1's claim, tested rather than assumed.
6. **`B-145`'s reading, confirmed or destroyed against a running terminal** — §4's caption finding. One line in the done-note.

**Part 0's list goes in the done-note.** It is the fact no document in this project currently states correctly, and the last two attempts to state it from outside the code were both wrong.

---

## 3. Part A — `B-144` first, because the panel is about to render it

**`B-144`, priority 1, status NEW.** `compute_context_and_rail`'s rail branch derives `prev_day = prior[-2]`, on the assumption that `prior[-1]` — `rth_dailies[-1]` — is today's session in progress. **`088` Part 0 established by reading `ibkr.py`'s `daily_bars` that this is false before the session's first RTH print**: the request issues `useRTH=True` with an empty `endDateTime`, so before RTH opens the last bar returned is a whole completed session.

**At a pre-open attach the rows labelled *prior session* carry the high and low of the session BEFORE the last completed one.** On a Monday pre-open attach that is Thursday's values where Friday's belong — **rendered as ordinary values, with no refusal and no marking.**

**04:00 ET is when Christoph actually attaches.** The screenshot that opened this task is a pre-open attach. **This must be fixed before `PDH`/`PDL` reach a rail, or the panel's first act is to render two wrong prices that look exactly like right ones.**

### The fix shape, and it is not `B-142`'s

**Do not copy `088`'s fix across.** `ADR% used` was **correct** to refuse: before the session opens there is genuinely no value to compute. **`PDH`/`PDL` are different — the correct value is present, in `rth_dailies[-1]`.** So:

- **Select the prior session by the daily bar's own date, never by position in the list.** B-023: never an index into an array where a timezone-aware ET date will do.
- **A refusal here would be a panel declining to render something it can compute.** Do not add one.
- **`088` already threads `today_et` into `Stage2Inputs`.** Reuse it; do not add a second clock source.
- **The `today_et == ""` escape hatch `088` built stays working** — every pre-088 test depends on it.

**Confirm red before green**, against the real defect: one `Stage2Inputs`, `today_et` fixed, `rth_dailies[-1]` dated **yesterday** (the pre-open case) and dated **today** (the intraday case) — `PDH`/`PDL` must name the same session in both. **That is the assertion; a test that only exercises the intraday case cannot fail on this bug.**

**`ext 10/20/50` are named in `B-144`'s own resolution field and are out of scope here** — nothing renders them, and they inherit `088`'s gate by sitting inside its `else` branch. **Do not touch them. Do not audit them. Say nothing new about them.**

---

## 4. Part B — the panel, built to mockup v1.5

**Open `LEVELS mockup — the rail against the running terminal - LATEST` in the Drive `Mockups/` folder and build from it. The mockup outranks the spec on layout** — B-122.

**The mockup's own banner names an unresolved duplicate:** `02 LEVELS mockup — the rail and its sortings` also claims `- LATEST` for this panel, dated 2026-08-16. **The file you build from is the one whose title begins `LEVELS mockup — the rail against the running terminal`.** Nothing has been moved and this task does not resolve that pair.

### The four rulings, from the mockup's §0

| | Ruling |
|---|---|
| **Window** | **One ADR above and below last price.** Levels outside it do not render. |
| **Amendment 1** | **Sort nearest to furthest and truncate at five — per side, independently.** Never a global sort. |
| **Amendment 2** | **The caption says what it is hiding** — two numbers, `5 of 23 · 18 outside 1 ADR`. |
| **Amendment 3** | **Hysteresis: a level enters at ≤ 1.00 ADR and leaves at > 1.10 ADR.** |
| **Amendment 4** | **ADR missing ⇒ the filter is off, everything renders, and the caption says why** — `filter off — ADR unavailable`, never a bare `filter off`. |

**Amendment 1 is the one that matters and the reason is not symmetry.** A global nearest-five can return five levels above price and one below, or none below. **On a fast move away from the day's structure, the side that empties is the side you are stopping against** — and the rail looks full while it does it.

**Amendment 3's asymmetry is the entire mechanism.** Equal thresholds do not reduce flicker, they relocate it. **A row must be harder to remove than it was to add.** **1.10 is unfitted** — nothing has measured how often levels sit near the boundary — **and it renders as unfitted wherever provenance shows.**

**Amendment 4 fails open deliberately.** The unfiltered rail is long and obviously unfiltered; a wrongly filtered rail is short and looks right. **Five rows, sorted, priced, and wrong about which five is a well-formed rail answering a different question.** `ADR% used` is `pending` for the first seconds of an attach and `unavailable` after a failed fetch — **the window has no basis in either case, and today it also refuses pre-open with `session not started` (088), which is a third case with the same answer: filter off.**

### Layout, from the mockup's §1

- **Furthest at the top, nearest at the bottom, on both sides**, with price rendered between the halves. The rail reads as a price axis laid flat: **the two rows adjacent to the divider are the two nearest levels — the ones a stop sits against. Reading order and physical position agree.**
- **`above` holds levels above price. The label describes price, never the trader** — side is declared in TRADE. B-112, closed, Option A.
- **Every distance is in dollars, signed. Nothing is normalised, fitted, ranked or scored.** ADR appears in the caption only; **no row is ADR-normalised** — v1.3's ruling stands.
- **A footnote rides on its row** — `gapped over — no trade there today` attaches to `PDC` where the row renders, never as a separate keyed line.
- **The token strips and the `next` row are gone.** Once every rendered row carries its own price and distance, a strip listing names without distances answers a question the rows already answer, and `next` is simply the row nearest the divider. **One fact under two names is what v1.4 deleted `clear for` to stop.**

### The caption is not the one the panel already has — `B-145`

**Read this before writing the caption, because the shape already on screen looks correct and is not.**

**`Panel.body()` renders `{len(shown)} of {len(self.rows)} · +K more ↓` when rows are hidden and `{len(self.rows)} of {len(self.rows)} · end` when none are.** `self.rows` is **every line the panel holds**. ATTACHED therefore counts its own `QQQ  attached 08:07:32` symbol line alongside the four `CONTEXT_ORDER` rows and renders **`5 of 5` over four value rows** — which is what a screenshot of the running terminal shows today.

**That caption is a SCROLL indicator wearing the shape of a CONTENT count.** They are two different facts: *how much of this panel fits on screen* and *how many of the things this panel is about survived a filter*. **This project's defining defect is one well-formed value answering a different question, and this is an instance of it in the shared panel chrome.**

**It matters here and not merely in the abstract.** The mockup's caption is `5 of 23 · 18 outside 1 ADR` — **a content count with a reason attached.** A line counter cannot produce either half. **A LEVELS panel that inherits the existing caption would silently report how many lines fit rather than how many levels the window kept, and the number would look entirely plausible while doing it.**

**So: LEVELS carries its own caption, computed from the level set and not from the rendered line count.** Both numbers, and the reason clause, come from the same computation that selected the rows.

**Do not fix ATTACHED's `5 of 5` here.** `B-145` is raised, unruled, and the choice between *give `Panel` a caller-supplied caption* and *exclude chrome lines from the count* is not this task's to make. **Confirm or destroy `B-145`'s reading against a running terminal — Part 0 item 6 — and leave ATTACHED as it stands.**

### The count, and it must add to twenty-three

**The denominator is what computed** — the mockup's §6 renders `4 of 17`, not `4 of 23`, with the failures as their own rows. **Rolling failures into the far-away count would hide a defect inside a preference.**

**This task adds a third category the mockup does not yet have, because only ten of the twenty-three are built.** Render it as **one grouped absent row**, in the mockup's own grouped-by-reason shape:

```
  absent      HOD LOD · PDO PDC · PWH PWO PWL PWC · MoMH MoMO MoML MoMC · ATH — not built
```

**`not built` and `session boundary unresolved in ET` are different reasons and must not render alike.** A level that was never written and a level that failed to compute are not the same fact, and the panel that conflates them is the panel that lets the first hide behind the second.

**Absent rows are not windowed.** A level with no price has no distance, so the filter cannot apply to it — **and a failure must not be able to hide by being far away.**

**The invariant, and it is the test that carries this panel:**

> **rendered + excluded-by-window + absent-with-a-reason + not-built = 23, on every paint.**

### Build the rows as a list

**Each row is one entry carrying its key, its label, how its value becomes a string, and what renders when it is absent.** **The panel renders the list; it does not know the rows individually.**

**This is not a refactor and it is not a framework.** It is how a new panel is written when the alternative costs nothing. **Do not generalise it, do not extract it into shared machinery, and do not touch any other panel** — `073` proposed exactly that and Christoph retired it on 2026-08-23.

**Resolved at import, immutable after. No runtime toggle and no config file for rows.** Christoph, 2026-08-23: *"Any information added or removed is at config time. The only exception is attaching to a symbol."* **A row that can be turned off at runtime is a refusal that can be turned off at runtime.**

**One test carries the value: a level absent from the list is absent from the record the renderer reads.** That is **`B-028` made impossible rather than caught** — the ADR dollar value kept arriving after its row was deleted.

### Fixtures first, and assertions that can fail

**Write the snapshot fixtures from the mockup before the panel, and see them red.** PROCESS §9, and **the step that gets skipped is step 3.** `070` and `071` both wrote fixtures after the code and both said so in their own notes. **This is the one that stops the streak.**

**And write assertions that can fail.** `071` found `"ATTACHING" in body` passed on two different wordings, so `070`'s claim of a match had never been tested. **Assert the rendered row exactly** — B-126 — **not by substring.**

---

## 5. Part C — height, measured rather than argued

**The mockup's §7 says the panel grows to thirteen lines at five per side, that the terminal is 209 × 54 drawing eight panels, and that whether thirteen lines fit is genuinely unknown rather than merely unverified** — the whole-screen mockup has not been redrawn at eight panels.

**Measure it and report the number.** If it does not fit, **use the fallback the mockup already names — keep the window and truncate at three per side, nine lines — and do not invent a third option under pressure.** Reintroducing the token strips is not available: it brings back the one-fact-two-names problem v1.4 deleted `clear for` to solve.

**Width stays unverified at 209 columns with ambiguous-width characters counted** — B-010, B-012. **Do not claim it verified.**

**Scratch for any measurement lives in `$env:TEMP`, never in the repo.**

---

## 6. Exit tests

**Green.**

- **Part 0's confirmed inventory is in the done-note** — the live `RAIL_ORDER`, the mapping onto the twenty-three, the `ATH` contradiction resolved, what `round` computes from, whether any of the ten reads a boundary `B-043` gets wrong, and `B-145` confirmed or destroyed.
- **`B-144` fixed by date selection, confirmed red first**, with the pre-open and intraday cases asserted to name the same session.
- **The LEVELS panel renders**, matching mockup v1.5, with **fixtures written first and seen red**.
- **Per-side truncation asserted with a deliberately lopsided fixture** — a case where a global sort would return five above and one below, and the panel returns five and five.
- **Hysteresis asserted across a sequence, not a single frame**: a level at 1.05 ADR that is already rendered stays; the same level at 1.05 ADR that was not rendered stays out.
- **The caption is a content count, asserted on a fixture where the line count and the content count differ.** A caption test that passes when the two happen to be equal has not tested anything — this is `B-145`'s own trap, and the fixture must make it visible.
- **`rendered + excluded + absent + not-built = 23` on every paint**, asserted.
- **A level removed from the row list is absent from the record the renderer reads.**

**Refusal.**

- **ADR pending, unavailable, or refused pre-open** ⇒ every computed level renders, filter marked off, **caption names the reason**.
- **A window unresolvable in ET** ⇒ every level from it absent with its reason. **Never a boundary drawn by bar position as a fallback.**
- **A session incomplete** ⇒ absent with its reason, **never a partial extreme.**
- **`not built`, `absent with a reason`, and `outside 1 ADR` render as three visibly different things.**
- **Nothing attached** ⇒ `not attached`, **never `0 of 23`**, and no price row.

**UAT (Christoph).**

- **Attach pre-open, around 04:00 ET, and read `PDH`/`PDL` against the previous session's actual high and low.** Then attach the same symbol after 10:00 ET and read them again. **They must name the same session.** This is `B-144`'s own repro and it is the one that matters most.
- **One name per built window where the extreme printed outside regular hours.** **An RTH high can never exceed the ETH high; an RTH low can never sit below the ETH low.** A value on the wrong side is a defect; **equality proves nothing** — B-093.
- **Read the caption against the rail on a quiet name and on a wide one.** The two numbers must agree with what is on screen — **count the rows.**

---

## 7. Not in this task

- **The session module, `B-043`.** Holidays and half-days. Its own task, and it comes before the thirteen.
- **The thirteen unbuilt windows** — `HOD LOD · PDO PDC · PWH PWO PWL PWC · MoMH MoMO MoML MoMC · ATH`. They render as `not built` here and are built after the session module.
- **ATTACHED's own `5 of 5`** — `B-145`, raised and unruled. **Confirm the reading; do not fix the caption.**
- **`ATH` and the request budget.** ATTACHED §3 allows three requests per attach and `058` collapsed the dailies to one 1Y series, which cannot establish an all-time high. **Do not add a fourth request and do not widen the 1Y one.** If Part 0 finds `ATH` genuinely renders today, **write a question file** naming what it costs in requests and duration, and continue.
- **Deleting `round`, or rendering it.** §2 item 4.
- **The eight other rail states** — B-078, untested · traded through · reclaimed · lost · direction-filtered · two levels at one price. The design session's to draw.
- **Whether the rail ever shows one side only** — B-083. Unruled.
- **`B-076`**, the ATR multiplier. Christoph's.
- **ATTACHED.** `071` landed and `087`/`088` corrected it. **Do not re-enter that panel.**
- **Any other panel's row structure.** §4.
- **`ext 10/20/50`.** §3.

---

## 8. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note carries Part 0's inventory, the `round` finding, `B-145`'s verdict, the measured panel height, and whether the fallback was used.** All five are facts about the tree that no document currently states, and the last two attempts to state any of them from outside the code were wrong.

---

**This note needs to be pasted to chat.**

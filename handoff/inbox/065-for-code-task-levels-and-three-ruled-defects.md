---
task: 065
class: product
depends: none
touches: live/attach/attach.py live/attach/ibkr.py live/tui/app.py live/tui/day_record.py live/tui/grammar.py live/tests/
---

# 065 — three levels restored, three ruled defects closed

**If `handoff/inbox/065-for-code-task-levels-and-three-ruled-defects.md` exists in your tree and `handoff/done/065-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Shape, and the one thing that is not decided yet

**Four pieces of work. All four are ruled — nothing here needs a decision from Christoph or from the design session.** Every value below comes from a product spec or a closed bug row.

| Part | Work | Ruled in |
|---|---|---|
| **A** | Restore ORL5, ORL15, 52wL — twenty levels becomes twenty-three | LEVELS v1.3 §2, B-017 |
| **B** | RVOL numerator and denominator on one basis | ATTACHED §3, B-049 |
| **C** | Replace path for the forming bar, never accumulate | ATTACHED §3, B-050 |
| **D** | ATR is 20-period and the label says so | ATTACHED §3 / §11.1, B-091 |

### **The partition is discovered, not asserted**

**`064` could name four disjoint files up front. This one cannot, and pretending otherwise would be the defect this project keeps cataloguing.** B, C and D all live near the attach and statistics path and may share a module.

**Part 0, before any subagent starts:** map each of A–D to the exact set of files it must write. **Report the map in the done-note.**

- **Parts whose file sets are disjoint run as parallel subagents.**
- **Parts whose file sets intersect run sequentially, in the order D → B → C**, because D changes a period that B and C then read.
- **Do not force parallelism onto a collision.** A partition that is asserted rather than measured is how two agents overwrite each other.

**No subagent commits or stages. The parent commits once, at the end.** Stated as a convention; it is weaker than a missing tool and should be treated as weaker. The real mitigation is the disjoint file sets Part 0 establishes.

### **Do not undo 058**

**Attach now runs on a Textual worker with an atomic swap, one paint, and an `[ ATTACHING SYMBOL ]` badge.** Every part below renders inside that. **A change that reintroduces a partial paint or a per-row trickle has broken a fix from yesterday**, and the existing attach tests must stay green.

### **Do not run concurrently with `064`**

One instance, one branch. **`065` and `064` touch disjoint files but share an index. Whichever runs second starts after the first has committed.**

---

## 1. Part A — the three levels come back

**LEVELS v1.3 §2 is authoritative and the ruling is closed.** *Christoph, 2026-08-22: "ORL5, ORL15 and 52wL are all intentional and to be rendered in the UI."*

**Twenty-three levels:**

```
today        HOD  LOD  ORH5  ORH15  ORL5  ORL15
prior day    PDH  PDO  PDL   PDC
pre-market   PMH  PML
prior week   PWH  PWO  PWL   PWC
prior month  MoMH MoMO MoML  MoMC
long chart   52wH 52wL ATH
```

**They are standing levels — definitions with no free parameters.** ORL5 and ORL15 are the lows of the same two opening-range windows whose highs are already computed. **52wL's bars are already fetched:** `058` Part 1 collapsed the daily requests into one 1Y request that serves 52wH, and 52wL comes from the same series. **No new request. If a part of this needs one, stop and say why** — that would contradict ATTACHED §3's three-requests rule.

**Every level is RTH.** LEVELS §1, task 041. **The session boundary is drawn in US/Eastern via zoneinfo, never by bar position** — B-023, and `attach.py` has already been wrong here once.

**The rail caption is `23 of 23`, and the refusal caption is `17 of 23`** — LEVELS §8. **Fewer-available and nothing-more-here must not render identically.**

**52wH, 52wL and ATH may be the same price and all three still render.** A level that vanished because another equalled it would read as a level that was never there.

**Not in Part A:** the rail's `▲ above` / `▼ below` labelling, which is a separate open defect, and the eight state mocks. **Render the three levels into the existing rail structure and change nothing else about it.**

---

## 2. Part B — RVOL, one basis on both sides

**B-049. ATTACHED §3:** *"useRTH defaults to True. Pre-market in the numerator and not the denominator reads 3× on an ordinary morning."*

**Required:** the numerator's session anchor and the denominator's 20-session curve are built on the same `useRTH` value, and **the anchor matches VWAP's.**

**This is the §7 archetype and fixtures cannot catch it.** A fixture is internally consistent by construction; the defect is in *which real request each side made*. **So the test asserts the call sites, not the output** — every historical fetch names `useRTH` explicitly, and the two RVOL sides name the same one.

**It refused once already and Claude Code said plainly the refusal was luck.** A minute earlier it would have rendered a plausible number. **Do not accept a passing render as evidence.**

**RVOL stays ratio-scale, median not mean, and `RVOL_rel` with no sector mapping renders `unavailable (no sector mapping)` — never 1.0.**

---

## 3. Part C — the forming bar is replaced, never accumulated

**B-050. ATTACHED §3: build the REPLACE path.** The forming bar is revised in place — 344 of 376 updates — and **both terms of Σ(WAP × volume) change on every update.**

**The measured cost of adding instead: VWAP off by +0.214¢, volume overstated 5.94×.**

**That asymmetry is why this one matters more than it looks.** The number you would sanity-check stays plausible while the one you would not is six times wrong. **The exposure is RVOL — a quiet name at 0.8 renders 4.8, and RVOL is a selection criterion.**

**The test that catches it:** reconstruct one session at two different attach times and require **identical cumulative volume and VWAP to the cent.** ATTACHED §3 — there is no such thing as a late attach.

**If the seam cannot be verified, VWAP renders `unavailable (splice unverified)`.** A VWAP off by three cents does not look broken and it becomes position size.

---

## 4. Part D — ATR is 20-period, and the label says 20

**B-091. ATTACHED §3, ruled twice and confirmed directly by Christoph on 2026-08-22: there is one ATR, it is 20-day, and it is ETH.**

| | ADR20 | ATR20 |
|---|---|---|
| Window | 20 sessions, excluding today | 20 sessions |
| Basis | **RTH** 09:30–16:00 ET | **ETH** 04:00–20:00 ET |
| Definition | Mean of (high/low − 1) × 100 | **Wilder RMA, α = 1/20** |

**The screen currently renders `ATR14`. Change the period to 20 and the label with it.** A label one character wrong is the defect this project keeps cataloguing.

**`ATR20` requires `useRTH=False` explicitly at its call site**, and a test asserts no fetch call site omits the parameter. **Getting it wrong returns RTH-only data silently.**

**Assert the bar count received.** B-033 — IBKR returned 204 for a request of 205 with no error, and a degraded supplier looks exactly like a quiet market. **A larger window is a larger request; do not assume it arrived whole.**

### **What Part D must not do**

**The 3× ATR stop floor is B-076 and it is Christoph's.** It was calibrated against RTH numbers and consumes an ETH ATR; **changing the period changes the input again.** **Do not re-derive, refit, or adjust the multiplier. Do not let the stop reprice silently on the back of this change.** If the stop table consumes ATR, it continues to refuse or remain blocked exactly as it does today, and the done-note states that B-076's refit now has a moved input.

---

## 5. Not in this task

- **B-076**, the stop multiplier. A threshold, therefore Christoph's.
- **B-043**, the session module built twice. Related and separately scoped — **do not fix it from inside this task**, and if Part A trips over it, say so and work around it rather than widening.
- **The rail's `▲ above` labelling** and **the LEVELS 15:59 / ATTACHED 16:00 boundary spelling.** Both are spec defects; the design session owns them.
- **The eight rail state mocks.** B-078, mine to draw.
- **`056`, the sync divergences, `verify.ps1`, `NOW.md`.** All `064`.
- **`.claude/settings.json`.** You cannot write it and must not route around that.

---

## 6. Exit tests

**Green.**
- **Twenty-three levels compute and render**, caption `23 of 23`, all six windows RTH, boundaries drawn in ET.
- **RVOL's two sides name the same `useRTH` at their call sites**, asserted by a test that reads the call sites rather than the output.
- **One session reconstructed at two attach times gives identical cumulative volume and VWAP to the cent.**
- **ATR is 20-period, ETH, Wilder RMA, labelled `ATR20`**, its request names `useRTH=False`, and its bar count is asserted.
- **058's attach behaviour is unchanged** — worker, atomic swap, one paint, the badge. Its tests still green.
- **Each part was seen red before green.**

**Refusal — none of these is optional.**
- **Fewer than twenty-three levels available** renders `17 of 23`, distinguishable from *nothing more here*.
- **A session boundary that cannot be resolved in ET** makes every level from that window absent with its reason — **never a boundary drawn by bar position as a fallback.**
- **Splice unverified** renders `VWAP unavailable (splice unverified)`.
- **No sector mapping** renders `RVOL_rel unavailable (no sector mapping)` — never 1.0.
- **A short bar response refuses.**

**UAT (Christoph).**
- **The twenty-three-token rail at 209 × 54.** Do the three restored levels fit on four lines, and is the caption right.
- **ATR reads `ATR20`** and its basis tail is legible — B-005/011 says that tail is the row the renderer cuts.
- **This does not close 013.** A fresh UAT against his own charts is separate and needs market hours.

---

## 7. The closing sequence

**Parent session only, after all parts report.** Per `CLAUDE.md`, from the main checkout. One commit.

**The done-note states the Part 0 file map** — which parts ran in parallel and which were serialised, and why. **That map is the finding most worth keeping**, because the next batch of product work will need it.

---

**This note needs to be pasted to chat.**

# S009a — The panel is never measured against the space it is given

**Status** WRITTEN · **Date** 2026-08-11 · **Type** defect fix + probe
**Runs in** `D:\Dev\momentum`. **Start after 16:00 ET**, once `012`'s capture has closed and released `clientId 11`.
**Found by** Christoph's `S009` UAT — `christoph/open/003-s009-read-the-empty-screen.md`. The UAT worked: it found three shipped defects a green suite did not.

> Read this cold. The session that wrote it cannot answer questions.
> **Part 4 needs a TWS restart and must not begin until the capture is finished and reported.**

---

## Why

`S009` shipped at 99 passed, 0 failed. Christoph then ran it on the machine he actually trades on and found **three defects and one absence**, all from one root cause:

**The panel is never measured against the space it is actually given.** `BOX_WIDTH` is fixed at 71 and tested in isolation; the caption is appended afterwards and nobody measures the sum; the too-small guard checks the *window* while the thing that breaks is the *tile*.

The suite is green because its three widths — 80, 120, 240 — **straddle the working width without covering it.** A test that passes at 240 and at 80 while the real screen is neither is a well-formed suite answering a different question.

---

## Part 1 — Three width defects

Evidence is in the UAT record; all four screenshots are the same code at four sizes.

**1a — the caption overruns the border, and it wraps.** At 1920×1080 maximized, **all six panels** wrap: `no ingest / today +`, `not / transmitted +`, `updates · none / yet +`. In SIZING and RISK the horizontal rule overruns too, leaving a stray `--` on the following line.

**This is not cosmetic.** The caption *is* the provenance — source, as-of time, safety state — and `SPEC.md` §4 calls a panel without a legible update stamp the `[ STALE ]` anti-state. A wrapped caption is provenance failing to render as one thing.

**Measure title + border + caption against the width available, and fit within it.** When it will not fit, **truncate or drop by a declared rule that renders the loss**, never by silent overflow. Say in the code which end gives way and why.

**1b — the body overruns when the tile is narrower than `BOX_WIDTH`.** Resized smaller, the panels rendered anyway: borders folded into four-line blocks, every value wrapped, entirely unreadable. `BOX_WIDTH = 71` is compared against nothing.

**1c — the too-small guard never fires, at any size.** Reduced to two rows, only the bottom tile row rendered and **no `window too small` appeared.** `S009` reports the guard tested at 40×10 against a `60×16` minimum, so the check exists — but a 1920 window split three ways gives each tile far under 71 columns while the *window* still satisfies `60×16`.

**The guard measures the wrong dimension.** Replace the fixed window minimum with a per-tile check at render time: **each tile is measured against what its panel actually needs.** Resolution-independent, and it is the real bug.

**When it fires, `S009`'s rule stands**: render the stated message and **zero panels — never a silently clipped one.** What shipped is exactly the silently clipped case the rule forbids.

---

## Part 2 — Pin the width that is actually used

**Christoph runs two monitors: 3440×1440 and 1920×1080, and 1920 is the likely working resolution.**

**Ask him for `$Host.UI.RawUI.WindowSize` at his working size and font, and pin that as the primary snapshot width.** Do not derive it from pixels — font size decides columns and only the terminal knows.

**Keep 80 as the floor and 240 as the ceiling; add the real width between them**, plus **one width below the per-tile minimum** asserting the too-small state renders and no panel does.

**Do not add a width without a reason recorded next to it.** A snapshot suite that grows by guessing is the list that becomes a hiding place.

---

## Part 3 — `NOT BUILT` renders nowhere, and that is the absence

Christoph asked whether there should be an indicator section. There should — with `S010` — and **nothing on screen says so.**

`NOT BUILT` is in `SPEC.md` §4's vocabulary and `S009` reports it reachable via `Cell.not_built()`. But a component absent from `config/layout.yaml` **does not render at all**, so a stage that exists in the spec and not in code is indistinguishable from a stage that does not exist. He had to ask.

**Same shape as *"nothing more here"* versus *"more below"*** — two different facts rendering identically. And it is the Layer 0 failure inverted: that rendered as built when it was not; this renders as nothing when it is merely not yet.

**The twelve stages are known and fixed** — ingest, regime, indicators, rank, `[HUMAN]`, size, stage, `[HUMAN]`, manage, reconcile, journal, archive.

**Declare every stage in `config/layout.yaml`, and render `NOT BUILT` with the slice that will fill it** — `NOT BUILT · S010`. The empty screen becomes a build progress report read every morning.

**Two constraints.**

**A `NOT BUILT` panel must be visibly a different kind of thing from a panel that has data and is refusing.** `— (no account snapshot)` means *the machinery exists and the input is missing.* `NOT BUILT` means *the machinery does not exist.* **Collapsing those would be the same defect this task is fixing.** No colour may carry the distinction (§4.1).

**Do not let unbuilt stages crowd out built ones.** Twelve panels on a 1920 screen at 71 columns will not tile. Give them a compact form — a single row each, or one panel listing them — and **say in the done-note what you chose and what it cost.**

**Regime is not a stage that is coming.** `SPEC.md` §3.2 removes every regime layer from the terminal. The health panel's `regime — (no file for today)` pointer is correct and must not become a `NOT BUILT` panel.

---

## Part 4 — After the capture: probe TotalView depth

**Only after `012` has closed, cancelled every subscription, disconnected, and released `clientId 11`.**

Christoph resolved `christoph/done/001`: the account needed the **NASDAQ TotalView-OpenView EDS Subscription Affirmation**, which permits API access to the deep book. He has added it. **It requires a TWS restart, deliberately deferred so as not to kill the capture.**

**After the restart, re-probe `reqMktDepth` on QQQ against `ISLAND`, then `NASDAQ`, then `ARCA`.** Same shape as `012a` Phase A: `numRows=10`, each cancelled before the next, **report the error code and dimensions on their face with no inference about the account attached.**

**This is post-session, and that is a variable rather than a known.** Whether depth is served outside regular hours, and how thin the book is, is **what this probe establishes** — do not assume either way. **A refusal at 16:30 does not establish a refusal at 09:30**, and saying so is the whole discipline this task inherits.

Report: which venues served, dimensions, and whether the affirmation changed the 10089. **If `ISLAND` now serves the book, tomorrow's `016` takes TotalView instead of ARCA** — the deepest book for a NASDAQ-listed name.

**Change no subscription. Sign up for nothing.**

---

## Do not

- Do not weaken or delete any existing snapshot; add.
- Do not use colour to distinguish `NOT BUILT` from a refusal.
- Do not make `regime` a `NOT BUILT` panel.
- Do not begin part 4 before the capture is closed and reported.
- Do not restart TWS while `clientId 11` is connected.
- Do not touch `records/tape/`, or re-derive anything from today's capture.
- Do not modify `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md`, or `HANDOFF-PROTOCOL.md`.
- Do not adopt any module from `live/`.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full `pytest` against `015`'s baseline. State the count and name any failure that is not `test_uat_has_a_file`'s five historical notes. |
| **Refusal A** | Claude Code | At a width below the per-tile minimum: the too-small state renders and **zero panels do.** This is the case that shipped broken. |
| **Refusal B** | Claude Code | A caption long enough to overrun: confirm it is truncated by the declared rule and **that the truncation is visible**, not silently absorbed. |
| **Refusal C** | Claude Code | Confirm a `NOT BUILT` panel and a data-absent refusal render **distinguishably without colour.** |
| **UAT** | Christoph | Re-run at 1920×1080 maximized and at the small size that broke. Confirm the captions no longer wrap, the too-small state appears, and that you can tell at a glance which stages exist and which are coming. Write the record to `christoph/`. |

## Done-note must state

- The pinned width, and Christoph's `WindowSize` output verbatim.
- The caption-fitting rule, and which end gives way.
- The per-tile minimum, and how it is derived rather than fixed.
- What compact form the unbuilt stages take, and what it cost.
- All three venue probes: code or dimensions, on their face.
- **Whether post-session depth availability differs from `012a`'s 05:07 ET result**, stated as an observation.
- **Anything in this task that diverged from what was on disk.**

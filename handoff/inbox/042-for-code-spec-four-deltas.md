---
id: 042
title: Four deltas 038 v1.0 did not carry
type: spec
class: admin
unblocks: S012 — the level rail cannot be built while the opening-range levels have the wrong names and the state colours are unruled
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 042 — four things `038` v1.0 did not carry

**Type: spec. Class: admin.** Small. Four rulings, no new mechanism.

**Why this file exists.** The design session wrote a v1.1 of `038` after v1.0 had already landed and
been built against. **`tools/sync_from_drive.py` refused to overwrite it, correctly** — `handoff/`
is copy-and-keep and nothing there ever moves. **The Drive copy has been trashed. The tree's `038`
stands as merged.** These are the four substantive deltas, arriving the only way they legitimately
can: as a new task.

**Run `038` first — it is already done. Run `041` before or after; they do not touch.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/042-for-code-spec-four-deltas.md` exists in your tree and
`handoff/done/042-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes — `OBS-046`.

---

## 1 — the opening range is two windows, not one

**`038` v1.0 named `ORH` and `ORL`. There are four levels, not two.**

| Level | Window (ET) |
|---|---|
| `ORH5` · `ORL5` | 09:30–09:35 |
| `ORH15` · `ORL15` | 09:30–09:45 |

**Both are RTH by definition** — the opening range is a regular-session object and this does not
change under `041`.

**Rename in place.** A bare `ORH` must not survive anywhere: it is a well-formed name answering two
different questions, which is this project's defining defect. **If a bare `ORH` is consumed
somewhere, report where rather than guessing which window was meant.**

**Note the composition property:** `ORH15 ≥ ORH5` and `ORL15 ≤ ORL5`, always, since the 15-minute
window contains the 5-minute one. **Assert it if it is cheap.**

---

## 2 — the unit is attached with no space

**Christoph's ruling. `038` v1.0 carried the units rule but not the spacing.**

```
0.19ADR      not   0.19 ADR
$733.14      not   $ 733.14
36%          not   36 %
6.1×         not   6.1 ×
14:41h ET    not   14:41 h ET
```

**One exception: share counts keep their space** — `280k sh`, because `280ksh` is unreadable.

**Extend `038`'s Part 5 test 4 rather than writing a second one.** Keep it scoped positionally to
the render layer; a repo-wide scan matches its own fixtures.

---

## 3 — `ADR%avail`, and three rows are deleted

**c015 §1.7.** `ADR used`, `ADR $` and `room up` / `room down` leave the panel.

**What replaces them is one row:**

```
ADR%avail  36%
```

**The percentage of the day's average range still available**, which is the reading Christoph
actually takes. **`room up` and `room down` measured the same quantity in dollars and invited being
read as `clear for`** — distance to the next obstacle — which is a different question entirely.

**`ADR` itself is not deleted.** It remains RTH, it remains the denominator for every ADR-expressed
distance, and the stop table consumes it. **Only the four display rows go.**

**If `room up` or `room down` is consumed by anything other than rendering, stop and report.**

---

## 4 — a state and a distance never share a colour

**`SPEC.md` §4.1 forbids verdict colour. This is narrower and additional.**

- `gapped over` — a **state**. One colour.
- `clear for 0.19ADR` — a **distance**. A different colour.
- `▲ above` / `▼ below` — **side**, not good and bad.

**Neither state nor distance is a verdict, and the colours must not imply one.** Two different kinds
of fact rendered identically is how a reader learns to stop distinguishing them.

**No new palette. Use what `SPEC.md` §4.1 already permits** — if it permits only one non-default
colour, say so and stop rather than inventing a second.

---

## Not in scope

No panel layout work — that is `S012`. No new levels. No change to any basis: `041` rules the
thirteen and this file changes none of them. **No re-litigating anything `038` settled.**

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran; the renamed opening-range levels and the spacing rule both seen red first |
| **Refusal** | Claude Code | `ORH15` with fewer than fifteen minutes of session elapsed renders `unavailable (window not closed)` — **never a partial range**. `038`'s rule that a level carries its validity time |
| **UAT** | Christoph | `c022` — at 09:37h ET, confirm `ORH5` renders a value and `ORH15` refuses with its reason |

---

## Report

1. **Every place a bare `ORH` or `ORL` was consumed**, and which window it turned out to mean.
2. Whether `room up` / `room down` were consumed by anything but rendering.
3. Whether `ORH15 ≥ ORH5` holds in the fixture.
4. Which colours `SPEC.md` §4.1 actually permits, and whether four distinguishable meanings fit
   inside them. **If they do not, that is a finding and a question for Christoph, not a licence to
   add a colour.**
5. The two reds, quoted.
6. **What you could not do**, and why. Empty is suspicious.

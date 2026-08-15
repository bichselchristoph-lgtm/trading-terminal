---
id: 041
title: The thirteen unruled levels are RTH — close OBS-051
type: spec
class: admin
unblocks: S012 — the level rail cannot render twenty-four levels while thirteen of them have no declared basis
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 041 — the thirteen unruled levels are RTH

**Type: spec. Class: admin.** Small. One ruling, its rationale, and a test.

**Closes `OBS-051`.** `038` ruled the day, pre-market, post-market and opening-range levels and left
thirteen undeclared. **They kept whatever basis they happened to have, which is not a decision.**

**Run `038` first.** This amends what `038` established.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/041-for-code-spec-thirteen-levels-are-rth.md` exists in your tree and
`handoff/done/041-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes — `OBS-046`. Do not remove another
session's.

---

## The ruling

**Christoph, 2026-08-15: these thirteen are anchored to RTH.**

| Group | Levels |
|---|---|
| Today | `HOD` `LOD` |
| Prior week | `PWH` `PWL` `PWO` `PWC` |
| Prior month | `MoMH` `MoML` `MoMO` `MoMC` |
| Long | `52wH` `52wL` `ATH` |

**Scope is exactly these thirteen. Nothing `038` ruled changes, and no statistic moves.**

- `PDH` `PDL` `PDO` `PDC` — RTH, unchanged
- `PMH` `PML` — 04:00–09:30, unchanged
- `AMH` `AML` — 16:00–20:00, unchanged
- `ORH5` `ORL5` `ORH15` `ORL15` — RTH by definition, unchanged
- `ADR` RTH · `ATR14` ETH · `VWAP`, `RVOL`, cumulative volume ETH anchored 04:00 — **unchanged**

**If anything in the tree suggests this ruling reaches further than the thirteen, stop and report.**

---

## Why — composition, and it is the stronger argument

**`PWH` is the highest price of the prior week, which must be the maximum of that week's `PDH`s.**
`MoMH` must be the maximum of the weeks. `52wH` the maximum of the months.

**`038` made `PDH` RTH. If `PWH` were ETH, the chain stops composing** — you would get a week whose
high is above every day inside it, and no row on the panel could explain why. **Break the chain
anywhere and the level rail stops being one structure.**

**`PWO` and `MoMC` follow automatically.** A week's open is its first day's open; a month's close is
its last day's close. Both are already RTH auction prints under `038`.

**`HOD` and `LOD` are the `PDL` argument exactly.** An ETH `HOD` on a gap-down morning *is* `PMH` —
one price, two names, no way to tell which you are looking at. **A level that can silently become
another level is the defect `038` exists to remove.**

**The thin-print argument supports the same conclusion and is weaker, so it is recorded second:** a
handful of odd lots at 03:00 should not set a price Christoph sizes against.

---

## The cost, recorded so it is not discovered later

**`52wH`, `52wL` and `ATH` will not match Christoph's TradingView chart** on any name whose extreme
printed outside regular hours. **He trades with ETH charts enabled.** On QQQ they agree today; on a
gap-and-fade small cap they will not.

**This is a known and accepted divergence, not a defect. Do not "fix" it later.** Record it in
`docs/observations/OBSERVATIONS.md` so a future session finds the reason rather than the symptom.

---

## What is deliberately still unruled

**The SMA stack — 10/20/50/200.** `OBS-051` also raised it. **Nothing in core consumes it:**
`ext 10/20/50` left the panel under the scope decision of 2026-08-14 (TradingView owns charting and
indicators), and the grader is frozen.

**Leave it RTH and leave it unruled. Ruling a value nothing reads is admin.** Note in
`OBSERVATIONS.md` that it must be ruled before anything consumes it.

**`OBS-051`'s own argument no longer holds and that is worth recording:** it reasoned that an ETH SMA
would put the two sides of the `ext` ratio on different bases. **`ext` no longer exists**, so the
ratio has no sides. The conclusion survives; the reason for it does not.

---

## The test

**One test, positional to the level definitions.**

Assert that each of the thirteen requests RTH bars, **by checking the request actually issued**, not
that a constant exists. `038`'s Part 5 test 1 already has this shape — extend it rather than writing
a second one.

**Seen red by inverting one.**

**Do not write a test that scans for the string `use_rth`** — it will match its own fixtures. The
self-reference trap has fired repeatedly in this project.

---

## Not in scope

No panel work. No new levels. No change to any statistic. **No change to the SMA stack.** No
`tws_order` changes.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with the extended basis test, seen red first with one of the thirteen inverted |
| **Refusal** | Claude Code | A level whose basis constant is missing renders `unavailable (no basis declared)` — unchanged from `038`, confirm it still holds for the thirteen |
| **UAT** | Christoph | `c021` — read `52wH` for one name whose extreme printed outside regular hours, and confirm the terminal and the ETH chart disagree **in the expected direction**. A disagreement is the ruling working |

---

## Report

1. What basis each of the thirteen used **before** this task. The present state is the finding.
2. Whether any of them derived from a shared helper that also serves a ruled level — **if changing
   the thirteen would move something `038` settled, stop and report.**
3. The red, quoted.
4. Whether the composition property now holds: **is `PWH` the maximum of its week's `PDH`s in the
   fixture?** Assert it if it is cheap; report it if it is not.
5. **What you could not do**, and why. Empty is suspicious.

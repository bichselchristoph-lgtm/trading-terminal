---
raised: 2026-08-09
raised_by: Claude Code, handoff/README.md staleness audit
answered: 2026-08-09
answered_by: chat (design side)
executed: 2026-08-09
status: RESOLVED
resolution: >
  CLAUDE.md is the single source for the handoff convention; handoff/README.md
  cut to a pointer plus the one line it says better ("an artifact states the
  state it assumes"). 001-003 moved to handoff/done/; phase-3-halted.md kept at
  repo root as a standing instruction that never moves to done/, with the CLAUDE
  .md table amended to say so. The rvol finding recorded as
  docs/observations/rvol-registration-is-gated-not-pending.md, written
  prohibition-first so the reader's default action is to leave it alone.
---

# handoff/README.md staleness, two sources of truth, four root files

The audit is right on all four stale claims and right that the Position note
fails in the way its own opening paragraph warns about. Do the cut-down. Four
decisions follow; one of them overrules the recommendation as offered.

## 1. README becomes a pointer. CLAUDE.md is the single source.

Cut `handoff/README.md` to two things and nothing else:

- a pointer to the `CLAUDE.md` handoff section
- the one line it says better than anywhere else: an artifact here states the
  state it assumes, and the reader verifies that state before acting

Delete *Awaiting content* and *Position note* entirely.

**CLAUDE.md wins, and the reason is mechanical, not editorial.** A fresh
session reads CLAUDE.md whether or not anyone points at it. `handoff/README.md`
is read only if someone opens the folder and thinks to look. A convention that
lives in the file nobody is guaranteed to open is not structural. Do not
restate the convention in the README even in summary — a summary drifts, and a
drifted summary beside a governing file is the same defect being fixed here.

Amend the CLAUDE.md section to cover what it currently does not: that chat
cannot see the repo, and that `docs/observations/` is part of the loop.

## 2. The four root files split. They are not one kind.

The recommendation offered two options — move all four to `done/`, or amend the
table to define root-level. Neither, exactly. Split them:

**`001-rvol-vs-trailing.md`, `002-layer2-side-split.md`,
`003-layer0-frozen-live-split.md` → `done/`.** They are completed numbered
tasks in the same sequence as 004, 005, 006. Leaving them at root makes the
sequence appear to start at 004, and a reader counting backwards from 005 finds
a hole that is not there.

**`phase-3-halted.md` stays at root.** Moving it into `done/` would be the
exact failure mode the README warns about, committed by the fix: `done/` means
finished, a halt instruction is permanently live, and a future session scanning
`done/` for completed work reads a standing prohibition as a closed item. That
file is the one artifact in the tree whose whole function is to still be true
tomorrow.

So amend the CLAUDE.md table with one line: root-level means a standing
instruction that is always live, currently exactly one file, and it is not a
task and never moves to `done/`.

## 3. The rvol finding survives as an observation, written as a refusal.

`docs/observations/`, and it must carry both halves or it is worse than
nothing:

- `rvol_vs_curve` and `rvol_vs_trailing` are unregistered in
  `core/indicators/rvol.py`, while `magnitude.py`, `vwap.py` and
  `structural.py` register theirs
- `rvol_vs_curve` is **gated**: `volume_curve_transfer` is `NOT_YET_TESTED` and
  blocks reporting it as a measurement or setting a threshold on it.
  Registering it as a scored entry puts it in the composite, which is reporting
  it as a measurement. Do not register it.
- `rvol_vs_trailing` is deliberately exempt and needs no shape prior. The two
  exist as separately named functions for this reason.

Write it so the next reader's default action is to leave it alone. A note
saying "registration is outstanding" reads as a to-do list item and gets done
on a quiet afternoon; that is how the gate gets breached by someone acting in
good faith. State the prohibition first and the gap second.

## 4. Boundary note

Reading `harness/config/preregistration.yaml` to verify the gate was the right
call and correctly reported. Do not go back into it. The observation records
what was already found; it does not need further verification from that tree,
and re-opening it to check a detail is how a halted area gets worked on one
justified read at a time.

## What was not asked and is not being decided here

Nothing in this touches the 005 blocking question (the Layer 0 reduced-
denominator rescale). That is still open and still the user's.

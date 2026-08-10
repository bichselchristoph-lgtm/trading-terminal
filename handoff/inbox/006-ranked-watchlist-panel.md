---
task: 006
title: Ranked watchlist panel — the first thing that renders
status: READY
written: 2026-08-09
depends_on: 004 (WatchlistSnapshot), 005 Phase A (regime header)
blocks: sizing, reconciliation
---

# 006 — Ranked watchlist panel

The first panel that draws. 004 built the door; nothing has yet shown what came
through it. This scores every name in the ingested watchlist against the
selected playbook, sorts, drops nothing, and puts it on screen with the regime
header above it.

**You do not need any other context.** Do NOT go looking for the
research/phase-3 work in this repo — unrelated, HALTED by user instruction.
`tests/test_incomplete_work.py` has 5 pre-existing failures belonging to it.
Leave them failing. If a file points you there, report and stop.

## Scope

The ranked table, its header, and the playbook selector. Terminal panel,
PowerShell, in-place redraw.

**Explicitly NOT in scope — deferred to a later task:** the attached-symbol
block in the lower half of mockup-03 (live tape, levels, defended-level
strengths, delta/speed/blocks, the five attach slots, news context). All of it
needs the live IBKR data stack, and none of it is needed for P1 safe manual
trading. Building the top half alone gets a working end-to-end path from CSV
drop to screen. Do not start the bottom half.

## Source specs

| Doc | ID |
|---|---|
| mockup-03-watchlist.html | `1EPWElYWbM_4vPTHwyj2TYUyOzOCx15An` |
| Dashboard Spec — Amendment 3: Playbooks, Base Assessment, Extension | `1hRdXQIxEWbk2QNWTI7ocGhcXf2CEpXpJQyPvD6LQFt8` |
| mockup-README.md — read first | `16gYlaRCd4paFnzVwrvSrAvJWflwBd1dh` |
| handoff/done/004-watchlist-ingestion.md — the API you consume | in repo |

## Settled — do not reopen

| Decision | Detail |
|---|---|
| Score, do not cut | Every name the user handed the system stays on screen, ranked. The ranking is a lens on the list, not a filter that hides names. 31 in, 31 displayed. |
| Everything wears its status | Fit scores are unfitted until a registered calibration says otherwise. Label them. They must not visually outrank a deterministic measurement. |
| Missing is missing | `n/a` with the reason, never a zero. A zero in a relative-strength column reads as weak performance, which is a finding the system does not have. |
| News is labelled, never scored | A headline sits in context with its timestamp. It cannot move a score or a size. |
| Deepvue metrics keep their prefix | `deepvue_rvol` is not either of the two RVOLs this codebase computes. The parser already applies the prefix; do not strip it for display in a way that lets it stand in for a computed value. |
| Recorded regardless | Every field is persisted whether or not it is displayed and whether or not the user trades the name. That archive is what later earns any inference at all. |

## The one design decision I want to argue

**Sorting by an unfitted score is a stronger claim than displaying one, and
mockup-03 does not label it.**

Each row honestly says `unfitted` next to its fit number. Good. But the *sort
order* encodes exactly the same unvalidated claim — "these are the names most
worth your attention today" — and carries no label at all, because rank order
does not look like an assertion. It is the first thing the eye uses and the
last thing anyone thinks to question. On a fast morning the user reads the top
three, not the status column.

Proposal: the header names the sort key and its status, e.g.
`sorted by: fit (unfitted)`. Cheap, one line, and it makes the strongest claim
on the panel the one that is labelled. Optionally offer a deterministic
alternative sort (`deepvue_rvol`, `gap%`) so there is a key available that is a
measurement rather than a prediction — but do not make that the default without
the user saying so; changing what he sees first is his call, not yours.

## Design notes — proposed, confirm before committing

**1. Staleness renders in trading days, and this closes 004's open item.**
004 left `age_days` as calendar days and said so: a Monday looking at Friday's
list reads 3, but it is 1 trading day stale. That decision belonged to the
panel, and this is the panel. Use `core/us_equity_calendar.py` for the trading-
day count. Show the trading-day figure as the headline; keep the calendar
figure available. Staleness is shown, never enforced — an unchanged watchlist
is a legitimate state (stable universe). Do not alarm, do not block, do not
force a re-drop.

**2. A forward-dated export shows as forward-dated.**
`age_days` can be negative — a Sunday-evening preparation for Monday. 004
reports rather than clamps, deliberately, because a clamped zero is invisible.
Render the negative case as its own state, not as `0`.

**3. Fit scoring uses only what is deterministic today.**
Amendment 3 §A3.5 puts base measurements and the extension indicator first
precisely because they need no fit. For a Deepvue-sourced watchlist the
available inputs are the exported columns (`deepvue_gap_pct`, `deepvue_rvol`,
`deepvue_adr_pct`, float, market cap) — real per-symbol values, usable
immediately. Compose the fit from those, declare the composition in the
playbook config, and label the composite unfitted. Do not invent a weighting
and present it as derived.

**4. Playbook is config, not code.**
Per Amendment 3 §A3.1 the playbook selects from existing components; it does
not introduce new kinds. The initial set is `intraday_orb`, `intraday_flag`,
`swing_ep`, `swing_vcp`, each with its own timeframe, entry, outcome horizon,
holdout and status. Long and short both. Switching playbook must visibly reset
anything derived from the previous one — a default carried across playbooks is
the same class of error as a trailing setting altering size.

**5. The regime header is inherited, not recomputed.**
The panel shows the Layer 0 / Layer 1 / Layer 2 state and the exposure cell
from 005, read from the cached session value. If 005's composite is still NOT
BUILT, the header says so and shows the vetoes and grid, which are real. Never
render a placeholder regime.

## Definition of done

- Every ingested symbol appears. Test with a snapshot of N rows that exactly N
  render, including rows with missing metrics.
- A missing metric renders `n/a` plus reason. Test that no code path
  substitutes 0, and a control proving a present 0 still renders as 0.
- Fit scores and any composite render with unfitted status visible. Test.
- The sort key and its status appear in the header. Test that the header names
  the actual key used, not a hardcoded string.
- Staleness renders in trading days, is never enforced, and a negative age
  renders as forward-dated. Three tests.
- Regime header reads the cached 005 value and does not trigger a recompute.
- Panel renders from an archived watchlist as well as a freshly ingested one —
  history resolves from `scanner_watchlists/`, never from the drop folder.

## Housekeeping — do this in the same pass

`mockup-README.md` indexes four sheets ("The four sheets"); the folder contains
five. `mockup-05-live-context.html` is missing from the table. The user has
confirmed the README is stale and the sheet stands. Add the row:

| `mockup-05-live-context.html` | Live session context | The three Layer 0 rows that keep moving, shown beside the frozen composite; the NOT BUILT refusal state |

Update the count in the heading, and the sheet order — 05 sits between 03 and
the attached-symbol block, per its own footer, not at the end. A stale
blueprint beside a governing spec makes a reader distrust both.

## Tenets this leans on

1 (distrust the data), 8 (fail loud, degrade gracefully), 11 (a changed source
lowers confidence, never discards).

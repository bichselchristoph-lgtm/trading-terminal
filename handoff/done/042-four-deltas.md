---
id: 042
title: Four deltas 038 v1.0 did not carry
type: spec
class: admin
owner: claude-code
depends: 038
---

**Status** RUNNING

# 042 — done. Three deltas built, one stopped on purpose.

**Parts 1, 2 and 3 are built. Part 4 is recorded and stopped**, because `SPEC.md` §4.1 offers a
market measurement **no colour at all — not one, zero** — and `042` says to say so rather than
invent a second. §5 has the reasoning.

**The refusal came for free.** The 2026-08-13 regression fixture runs to 09:35, so its
15-minute window never closes and `ORH15` refuses against the same fixture that produces the
externally-verified numbers. **Nothing was staged to make that happen.**

---

## 1 — every place a bare `ORH`/`ORL` was consumed, and which window it meant

**All of them meant the 5-minute window, unambiguously. There was nothing to guess.**

| Where | What it was |
|---|---|
| `core/indicators/context.py:633` | `hi_lo(opening_range, "opening-range", "09:30-09:35 ET, today")` — **the producer.** The window was already in the sample string |
| `live/attach/attach.py:628` | `[b for b in today if "09:30" <= _clock(b.ts) < "09:35"]` — **the slice.** The only opening-range slice that has ever existed in this tree |
| `live/tui/app.py:351` | `RAIL_ORDER` — render order |
| `live/tests/test_attach.py:227` | asserted `{"…","ORH","ORL",…} ⊆ rail` |
| `live/tests/test_attach_is_reachable_by_key.py:694-698` | `034`'s UTC/ET regression — asserted `"5 opening-range bars"` in the sample |
| `live/tests/test_qqq_2026_08_13_regression.py:56-57,163-166` | `ORH = 726.02`, `ORL = 724.03`, checked against Christoph's IBKR chart |
| `live/tui/day_record.py:70`, `config/formatting.yaml:68`, three docstrings | prose mentions |

**Every one is now `ORH5`/`ORL5` and the values are untouched** — the window they were computed
over was always 09:30–09:35, so this is a rename and not a re-measurement. `ORH15`/`ORL15` are
new. `test_a_bare_orh_or_orl_does_not_exist` asserts neither bare name is in the rail.

---

## 2 — were `room up` / `room down` consumed by anything but rendering? **No.**

`room_left()` returned a pair that went straight into `out["room up"]` and `out["room down"]`
and nowhere else. Both rows are deleted.

**But `ADR $` was, and that is the one that would have broken quietly.** `042` deletes it as a
*display row* and says explicitly *"`ADR` itself is not deleted"*. Two live consumers:

1. `adr_available()` divides by it — `ADR%avail` is `100 − used`, and `used` is `|price −
   open| / ADR$`.
2. `level_rail(adr_dol=…)` spans `round` with it — *half-dollar levels within ±ADR$ of price*.

The second reached it through `out.get("ADR $")`, **the dict the panel renders from.** Removing
the row without moving the value would have blanked `round` with `no ADR $ to span` — a
correctly-worded refusal on a row nobody touched. `dol` is now passed directly from the local,
with a comment saying why it is not a dead variable.

`test_a_partial_adr_is_impossible_by_construction` now asserts `round` blanks when the daily
request fails, which is the invariant `ADR $` used to carry.

**`room_left()` itself is kept and now has no caller.** Deleting it would lose the argument in
its docstring — *a name that has used 90 % of its budget upward has very little room up and a
great deal down, and one number cannot say that* — which is correct and is the kind that gets
re-derived badly. Its docstring now says the rows were deleted, why, and **not to re-add them**:
the fault was never the arithmetic, it was that the rows measured `ADR used` in dollars and
invited being read as `clear for`.

---

## 3 — does `ORH15 ≥ ORH5` hold in the fixture? **It cannot be evaluated there.**

**`live/tests/test_qqq_2026_08_13_regression.py` builds bars from 04:00 to 09:35**, so the
newest bar starts at 09:34. The 15-minute window has not closed and `ORH15` refuses. **The
property is unevaluable in the fixture, not merely untested.**

**And it would have proved nothing even if the window had closed.** Both extremes sit in the
09:30 bar — `hi, lo = (ORH, ORL) if minute == 9*60+30 else (725.0, 724.5)` — so `ORH15` would
equal `ORH5` exactly. **Containment holding as equality is consistent with a rail that sliced
both windows identically**, which is the defect the two-window split exists to prevent.

**I did not extend the fixture, and that is the finding.** Adding ten minutes of bars means
inventing values nobody read off a chart, inside the one file in this repo whose authority is
that it was checked externally — and the invented bars would sit beside the verified ones,
indistinguishable. **`OBS-061`** holds it open; what would settle it is a second chart reading
from Christoph covering 09:35–09:45.

**The property is asserted instead in `core/tests/test_opening_range_windows.py`**, against bars
built so the two windows genuinely disagree — the high at 09:40, the low at 09:42:

```
ORH15 101.50  >  ORH5 100.04
ORL15  98.10  <  ORL5  98.96
```

`test_and_the_two_windows_actually_differ_here` exists specifically so the containment assertion
cannot pass trivially. **That tests the arithmetic and not the market**, and the distinction
matters: it would pass against a rail slicing the right windows out of the wrong series, which
is exactly what `034` shipped.

---

## 4 — the two reds, quoted

**Neither was staged.** Both fell out of the change itself, which is what `042`'s exit test asks
for — *the renamed opening-range levels and the spacing rule both seen red first*.

**The rename:**

```
E           KeyError: 'ORH'
FAILED live/tests/test_attach.py::test_a_clean_attach_fills_the_context_block
FAILED live/tests/test_attach_is_reachable_by_key.py::test_the_opening_range_is_eastern_and_not_the_wire_format
FAILED live/tests/test_qqq_2026_08_13_regression.py::test_the_four_matched_levels_still_match
```

**The spacing:**

```
E       AssertionError: assert '1.4ADR' == '1.4 ADR'
E         - 1.4 ADR
E         ?    -
E         + 1.4ADR
FAILED live/tests/test_rendered_rows_declare_basis_and_unit.py::test_the_formatter_matches_spec_4_0a[adr-1.44-1.4 ADR]

E       AssertionError: these rows render a bare number with no unit:
E           ext 10: 0.0ADR
E           ext 20: 0.0ADR
E           ext 50: 0.0ADR
E         **All numbers need units** (038 Part 2). Expected one of: '$', '%', ' ADR', '×', ' sh', ' levels'.
```

**The second one is the interesting one.** `038`'s test 4 held `" ADR"` — *with the space* — in
its `UNIT_MARKS` tuple, so closing the space made three rows read as having no unit at all.
**A units test that encodes the spacing it is not testing.** Both were updated together, and
`042` Part 2's rule is now data rather than a literal: a `SPACING` table of
`(unit, marker, space_before)`, parametrised, so `sh` and ` levels` keeping their space is a
declared exception rather than an omission.

**Extended, not duplicated** — `042` says so explicitly. Scoped positionally to `FORMATS`; a
repo-wide scan for `" ADR"` would match the test's own docstring, which is the self-reference
trap `038` and `039` both tripped.

---

## 5 — which colours §4.1 permits, and whether four meanings fit. **They do not. Zero fit.**

**§4.1 binds colour to KIND, not to the thing being said:**

| Colour | Kind it belongs to | Available today? |
|---|---|---|
| **blue** | rule / parameter — a declared value inside its band | yes |
| **amber** | rule — outside a declared band, `enforcement: warn` | yes |
| **green** | **fitted** signal, measured against pre-registration, held | **no — nothing is fitted** |
| **red** | the same, failed | **no — nothing is fitted** |
| **dim + inverse badge** | the system refusing | yes |
| **red-inverse badge** | the one blocking rule | yes |

**`gapped over`, `clear for 0.19ADR` and `▲ above` are none of these kinds.** They are
measurements about the market — not rules against a declared threshold, not fitted signals, not
refusals. **§4.1 has no entry for a measurement, so it offers them no colour at all.**

**So `042` Part 4's ruling is satisfied vacuously today.** All three render in the default
foreground: they do not conflate with a verdict, and they do not distinguish from each other
either. **I recorded the ruling and stopped**, which is what Part 4 instructs.

**This is a finding and a question for Christoph — `OBS-059`.** Two ways out, and the second is
almost certainly right: either §4.1 gains a *measurement* kind, which reopens the question §4.1
exists to have closed, or **the distinction is carried by typography, glyph or position — which
§4.1 already requires anyway**, since *"colour is still never the only channel"* for colourblind
readers. **I did not pick**, because choosing would set the precedent that a palette rule can be
widened by whoever next needs a colour, and that is how §4.1's predecessor filled the screen.

---

## 6 — what I could not do

- **Part 4 is recorded, not implemented.** §5. `S012` will hit it.
- **The `HH:MMh ET` row of the units table has no consumer** and I did not build one. There is
  no `Unit.TIME`; `config/formatting.yaml` declares six units and no clock, and every time on
  the panel is a string built at its call site. **So the one unit rule motivated by an actual
  incident — `034` losing four values to UTC/ET — is the one the formatter cannot enforce**, and
  `test_every_rendered_number_carries_a_unit` cannot see it, because it iterates `Measured`
  values and a time is not one. `OBS-060`.
- **The regression fixture is not extended to 09:45.** §3. `OBS-061`.
- **`c022` is not performable as written** — *at 09:37h ET, confirm `ORH5` renders a value and
  `ORH15` refuses with its reason*. That is exactly right and the code does it; it needs a live
  session at 09:37, so it is a real UAT and not a gap. No file exists in `christoph/`, which is
  the design session's to author.
- **No panel layout work**, per `042`. `CONTEXT_ORDER` and `RAIL_ORDER` changed membership only.
- **`ADR%avail` has never been rendered against live data.** It is derived from `adr_used`,
  which `038` verified; the subtraction is new and only fixtures have exercised it.

---

## 7 — test results

**Full suite in `D:\Dev\momentum` after the merge:**

```
8 failed, 423 passed, 1 warning in 31.72s
```

**431 collected, of which 9 are this task's** — 8 in `core/tests/test_opening_range_windows.py`
and 1 added to `test_rendered_rows_declare_basis_and_unit.py`, all parametrised cases counted.
The tree stood at 422 / 8 / 414 after `039`. **The failure count did not move**, and the eight
are the tree's standing failures, unchanged.

`verify.ps1` ran as the last action and its output is not pasted, per `042`.

**In the worktree, before the merge: `11 failed, 420 passed`.** Eight are the tree's standing
failures and **three are worktree artefacts** — `test_evidence_carry_intact` (×2, the CRLF
anomaly of `OBS-033`) and `test_sync_from_drive` (`OBS-039`, an absolute path outside the
worktree) — plus `test_spec_pointers`. **None is from this task**, and every test that went red
from the change (§4) is green.

---

## 8 — the ledger

Three rows: **`OBS-059`** (§4.1 has no colour for a measurement — the one that gates `S012`),
**`OBS-060`** (`HH:MMh ET` recorded and unenforceable), **`OBS-061`** (the externally-verified
fixture cannot check the 15-minute window and must not be extended by invention).

**No id collision this time.** `039`'s `OBS-058` records that two sessions allocated `OBS-053`
to different findings on the same day and that nothing checks ledger ids for uniqueness; I
checked `main` and the worktree agreed at 058 before allocating. **That check is still a manual
habit and `OBS-058` is still open.**

---

## Files

| path | change |
|---|---|
| `core/indicators/context.py` | `level_rail` takes two opening windows and a `session_clock`; `ORH5`/`ORL5`/`ORH15`/`ORL15`; the not-closed refusal; `adr_available()` added; `room_left()` kept with a do-not-re-add note |
| `live/attach/attach.py` | slices both windows; passes the session clock; `ADR%avail` replaces four rows; `ADR $` passed directly to `level_rail` rather than through the render dict |
| `live/tui/app.py` | `CONTEXT_ORDER` and `RAIL_ORDER` |
| `config/formatting.yaml` | `adr` suffix `" ADR"` → `"ADR"` — the only unit with a leading space |
| `docs/specs/SPEC.md` | §4.4a.1 amended to four levels + the refusal; §4.4a.4 spacing rule; §4.4a.4a new, `ADR%avail`; §4.4a.5 gains Part 4's ruling and the stop |
| `live/tests/test_rendered_rows_declare_basis_and_unit.py` | test 4 extended with a parametrised `SPACING` table |
| `live/tests/test_attach.py`, `…_is_reachable_by_key.py`, `…_qqq_2026_08_13_regression.py` | renames; the 15-minute refusal asserted against the verified fixture |
| `core/tests/test_opening_range_windows.py` | **new.** 8 tests — containment, that the windows differ, and five refusal cases |
| `tests/test_adoption_log_complete.py` | one allowlist entry; the count is now 48 |
| `docs/observations/OBSERVATIONS.md` | `OBS-059` … `OBS-061` |

---

## Exit tests

| test | who | state |
|---|---|---|
| **Green** | Claude Code | **Done.** `verify.ps1` ran; the renamed levels and the spacing rule both seen red first (§4), and neither red was staged |
| **Refusal** | Claude Code | **Done.** `ORH15` with fewer than fifteen minutes elapsed renders `window not closed — 09:30-09:45 ET, today needs 09:44, session at 09:34`, never a partial range. Asserted in `core/tests/test_opening_range_windows.py` at 09:33 and 09:34, with no clock at all, **and against the 2026-08-13 fixture** |
| **UAT** | Christoph | **`c022`** — at 09:37h ET, confirm `ORH5` renders a value and `ORH15` refuses with its reason. **Performable.** No file exists in `christoph/` yet; that is the design session's to author |

---

## THIS NOTE NEEDS PASTING TO CHAT

**Writing it is not reporting it.** Three things the design session cannot get any other way:

> **1. Part 4 is stopped, as instructed.** §4.1 gives a market measurement **zero** colours, not
> one — blue is a parameter, amber a failed rule, green/red are fitted-signal-only and nothing
> is fitted. The distinction has to be carried by typography, and confirming that needs
> Christoph. **`OBS-059`, and it gates `S012`.**
>
> **2. The externally-verified fixture cannot check `ORH15`** and must not be extended by
> inventing bars. **A second chart reading for 09:35–09:45 is what would settle it.**
>
> **3. `038`'s own units test encoded the spacing it was not testing** — `" ADR"` with the space
> sat in its `UNIT_MARKS`, so closing the space made three rows read as unitless. Fixed by making
> the spacing rule data rather than a literal.

---
id: 065
title: ATR moved to 20-period; RVOL, VWAP and three named levels were already correct
type: task
class: product
owner: claude-code
depends: none
touches: core/indicators/context.py live/attach/attach.py live/attach/ibkr.py live/tui/app.py live/tests/test_attach.py live/tests/test_attach_is_reachable_by_key.py live/tests/test_qqq_2026_08_13_regression.py
bugs:
  - id: B-091
    action: close
    status: fixed -- ATR moved to 20-period, ETH, label ATR20
  - id: B-049
    action: confirm
    status: already fixed -- RVOL numerator/denominator already share useRTH; a call-site test already existed and was already green
  - id: B-050
    action: confirm
    status: already fixed -- VWAP/cumulative volume already pure replace, never accumulate; the seam test already existed (S010 part 4) and was already green
  - id: B-017
    action: confirm
    status: ORL5, ORL15 and 52wL already rendered before this task; the row's wider 23-level scope is blocked, see handoff/questions/065-levels-panel-scope.md
---

**Status** RUNNING

# 065 — done for B, C, D. Part A blocked on a question; its own exit test needs work its own instruction forbids.

**Part 0's file map, before anything else, per the task's own requirement.**

| Part | Files it needed | Ran |
|---|---|---|
| A | none — investigation showed no code change was needed for the three named levels; the exit test's remaining scope is blocked, see the question | — |
| B | none — investigation only; no production file needed a write | investigated first |
| C | none — investigation only; no production file needed a write | investigated first |
| D | `core/indicators/context.py`, `live/attach/attach.py`, `live/tui/app.py`, `live/attach/ibkr.py` (comments), `live/tests/test_attach.py`, `live/tests/test_attach_is_reachable_by_key.py`, `live/tests/test_qqq_2026_08_13_regression.py` | ran after B/C confirmed clean, since it is the only part that touches shared files |

**Not run as parallel subagents.** Once B and C turned out to need no production write, D was the
only part touching files at all, so there was no collision to partition around — the map above
is what Part 0 asked for, and the honest answer is that three of the four parts needed no file
map because they needed no edit.

---

## Part A — blocked. See `handoff/questions/065-levels-panel-scope.md`

**Checked directly before touching anything:** `ORL5`, `ORL15` and `52wL` — the three levels
Part A names as missing — already compute and already render. `core/indicators/context.py`'s
`level_rail()` has always returned all three; `live/tui/app.py`'s `RAIL_ORDER` has always listed
all three; a live fixture attach returns real values for all three with correct basis labels.
**No code change was needed for what Part A's instruction literally asks for.**

Part A's own exit test (`23 of 23` / `17 of 23` caption, all six level categories) needs
thirteen more levels that do not exist anywhere in the tree — `HOD`, `LOD`, `PDO`, `PDC`, `PWH`,
`PWO`, `PWL`, `PWC`, `MoMH`, `MoMO`, `MoML`, `MoMC`, `ATH` — and Part A's own instruction text
("render the three levels... change nothing else about it") explicitly forbids building them.
**That contradiction is not mine to resolve by guessing which half of the task is authoritative,
so it did not get resolved by guessing.** Full detail, including that all thirteen are derivable
from data already fetched (no new IBKR request either way), is in the question file.

**One cheap thing was still worth doing and is not blocked on the question:**
`test_a_clean_attach_fills_the_context_block` checked `ORL5`/`ORL15` were present but not
`52wL`, and didn't assert any of the three actually measured (`.ok`) rather than merely being
present-but-absent. Added both. Seen green immediately — nothing was red, because nothing was
broken.

## Part B — already correct. No code change.

**B-049's own requirement** — the numerator's session anchor and the denominator's curve share
one `useRTH` value, matching VWAP's — is already enforced by construction:
`live/attach/ibkr.py`'s `today_minutes()` and `intraday_sessions()` both take their `use_rth`
from the same `INTRADAY_BASIS.use_rth` constant (`core/indicators/context.py`, `use_rth=False`,
whose own docstring states *"RVOL must match ITSELF: today's numerator and the 20-session
denominator on the same basis"*). `live/tests/test_attach_is_reachable_by_key.py` already asserts
`{k["useRTH"] for k in asked if k["barSizeSetting"] == "1 min"} == {False}` against the real
`IBKRMarketData` class and a fake transport — the exact "assert the call sites, not the output"
shape Part B asks for, not a fixture that could be internally consistent by construction. It was
already green.

`rvol_curve` is already median over the last 20 sessions (not mean); `rvol_at`/`rvol_rel` are
already ratio-scale (`Unit.MULTIPLE`); `rvol_rel` already refuses by name (`"no sector mapping"`)
rather than rendering `1.0` when there is no sector ETF, and
`test_rvol_rel_refuses_by_name_and_never_renders_one_point_zero` already covers it. **No code
change made; none was needed.**

## Part C — already correct, and older than this task. No code change.

`live/tests/test_attach.py::test_the_seam_two_attach_times_agree_to_the_cent` already exists,
predates this task (its docstring is dated to "S010 part 4," well before `038`/`041`/`058`), and
is the exact test Part C describes: *"There is no such thing as a late attach... attaching at
09:45 and at 10:12 must produce identical numbers for the overlapping window."* Its sibling,
`test_a_double_counted_seam_is_visible_in_cumulative_volume`, proves the fixture can fail (a
deliberate double-count changes cumulative volume) so the agreement test isn't vacuous.

The reason this holds structurally, not by luck: `vwap_from_bars()` and `cumulative_volume()`
are pure functions over whatever bar sequence they are given, and `live/attach/ibkr.py` has no
`keepUpToDate` subscription or any other incremental/streaming bar accumulation — every attach
issues a fresh `reqHistoricalData` call and sums the array it gets back, once. **There is no code
path in this architecture that could accumulate a forming bar**, which is the specific failure
mode Part C is written against. Both tests were already green.

## Part D — the one real defect. Fixed.

`ATR_DEFAULT_N` was `14`; changed to `20` (`core/indicators/context.py`), matching Christoph's
2026-08-22 ruling: one ATR, 20-day, ETH. The basis was already correct (`ATR_BASIS.use_rth =
False`, already required explicitly at its one call site, already tested by
`tests/test_session_basis.py`) — only the period and the rendered label were wrong.

**Renamed the rendered key, not the function.** `live/attach/attach.py`'s `out["ATR14"]` →
`out["ATR20"]`; `live/tui/app.py`'s `CONTEXT_ORDER` entry likewise. `atr_d14()` keeps its
internal name — renaming every caller and docstring that says "Wilder's ATR" is a larger,
unscoped change than a label fix, and the task's own wording ("a label one character wrong is
the defect") is about what renders, not about an internal identifier.

**Added `test_atr_is_20_period_by_default_and_refuses_a_short_series`** (B-033): pins
`ATR_DEFAULT_N == 20`, confirms 20 daily bars (19 true ranges) refuses naming
`"need 21 daily bars, have 20"`, confirms 21 bars computes, and confirms the sample string
actually says `n=20` — a bare value check would have passed even if the period silently stayed
14, because the QQQ regression fixture's true range is constant across every bar and Wilder's RMA
of a constant series is that constant at any window length.

**Seen red, then green, on the one assertion that could tell them apart.** Before the
`ATR_DEFAULT_N` edit, `assert "n=20" in whole.sample` failed (`"n=14"` was there instead); every
other assertion in that test would have passed at either period, which is exactly why the
`n=20`-in-sample check was added rather than trusted to the value comparison alone.

**Updated three existing test files' key references** (`ATR14` → `ATR20`, the rendered key, not
the historical prose): `live/tests/test_attach.py` (3 sites), `test_attach_is_reachable_by_key.py`
(2 sites), `test_qqq_2026_08_13_regression.py` (2 sites, plus the test function renamed to
`test_atr20_is_extended_hours_and_reads_about_15_6`). **Left untouched, deliberately**: every
place describing the *historical* 038-era defect — Christoph's real `13.14` vs `~15.6` TWS
comparison — still says `ATR14`, because that is what was actually measured at the time; rewriting
history to say `ATR20` there would be dishonest about what the regression fixture is pinned
against. `test_atr_is_wilder_not_a_simple_mean` was decoupled from the global default by passing
`n=14` explicitly, so a future retune of `ATR_DEFAULT_N` cannot silently change what that
unrelated (RMA-vs-simple-mean) test compares.

**No B-076 consumer exists to protect.** Searched the tree for anything that reads ATR into a
stop calculation — `live/tests/test_attach.py::test_the_attach_path_imports_no_sizing_or_staging_module`
confirms directly, in its own docstring, that no sizing or staging module exists yet. There is
nothing today that could reprice silently on the back of this change; the instruction not to
touch B-076 was honored by there being nothing there to touch.

---

## Full-suite evidence

`live/`, `core/`, and `tests/test_session_basis.py` together: **217 passed**, up from 215 before
this task (the two new tests: the ATR period/bar-count test and the strengthened
`ORL5`/`ORL15`/`52wL` assertions replaced a subset of an existing assert, net +1 test function).
No test that was passing before is failing now. The full repo-wide suite was not re-run as part
of this note — `065`'s own closing sequence runs `verify.ps1`, which does that.

**058's attach behaviour is unchanged**, confirmed by the full `live/` pass including every
`test_tui_measured_against_its_tile.py` and `test_attaching_state.py` case: worker thread, atomic
swap, one paint, the badge — none of this task's edits touch `app.py`'s attach dispatch, only its
`CONTEXT_ORDER` tuple.

---

## Exit tests

| test | result |
|---|---|
| Twenty-three levels compute and render, caption `23 of 23` | **blocked** — see question |
| RVOL's two sides name the same `useRTH` at their call sites | **already true**, pre-existing test |
| One session reconstructed at two attach times gives identical VWAP/volume | **already true**, pre-existing test |
| ATR is 20-period, ETH, Wilder RMA, labelled `ATR20`, `useRTH=False` explicit, bar count asserted | **true**, this task |
| 058's attach behaviour unchanged | **true** — full `live/` suite green |
| Each part was seen red before green | **true for D** (the `n=20`-in-sample assertion); **not applicable to A/B/C** — nothing was red because nothing was broken, and the done-note says so rather than fabricating a red run against code that already worked |

**Refusal exit tests** (`17 of 23`, ET-resolved boundary refusal, `splice unverified`, `no sector
mapping`) — the sector-mapping and boundary refusals already exist and pass (`test_rvol_rel_...`,
`test_the_fifteen_minute_range_refuses_because_the_window_never_closes`); the `17 of 23` caption
and `splice unverified` states are both downstream of Part A's blocked scope and Part C's
already-pure design respectively (there is no splice to fail-unverified in an architecture with
no accumulation) — not built, and not fabricated to look built.

**UAT (Christoph).** §6 asks him to read the twenty-three-token rail and confirm `ATR20`'s basis
tail is legible. **The rail still has ten levels, not twenty-three** — the UAT as written needs
Part A resolved first. `ATR20`'s own rendering can be checked independently of that.

---

## The closing sequence

**Parent session only, per `CLAUDE.md`, from the main checkout. One commit.**

- `sync.ps1` was not run again during this task (it had already run to fetch `065` itself).
- `verify.ps1` runs after this note, as the last action before commit.
- `export-handoff.ps1` runs after the commit, so its manifest HEAD is that commit.
- Push to `origin` (`trading-terminal`).

---

**This note needs to be pasted to chat**, alongside `handoff/questions/065-levels-panel-scope.md`.

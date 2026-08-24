---
id: 090
title: The LEVELS panel — render the ten that already compute, against mockup v1.5
type: task
class: product
story: S033
epic: 5
owner: claude-code
supersedes: 077
depends: none
touches: the level rail's prior-day selection, a new LEVELS panel and its caption, the app's panel set
mockup: LEVELS mockup — the rail against the running terminal - LATEST (v1.5)
uat: none declared in the task file
bugs:
  - id: B-144
    action: close
    status: "Fixed. `compute_context_and_rail`'s rail branch derived `prev_day = prior[-2]` unconditionally, assuming `prior[-1]` (`rth_dailies[-1]`) was always today's session in progress — false before RTH's first print, per 088's own Part 0 finding: `daily_bars`'s `endDateTime=\"\"` request answers 'now' with the LAST COMPLETED session. At a pre-open attach `prior[-1]` already IS the prior session; `prior[-2]` names the one before that. Fixed by selecting the prior session by the bar's own date against `today_et` (088's field, reused, not a second clock), falling back to the old positional behaviour when `today_et==\"\"` — every pre-088/pre-090 test keeps working unchanged. Confirmed red against the exact repro the task named: one `Stage2Inputs`, `today_et` fixed, `rth_dailies[-1]` dated yesterday and dated today — `PDH` must name the same session in both, and did not before the fix (103.0 instead of 104.0)."
  - id: NEW
    action: raise
    status: "`live/tui/app.py`'s `Panel.body()` renders `+K more ↓` (the scroll-truncation indicator) with NO `ascii_safe()` guard, unlike every other special character on screen (the box rule, the corners, the ellipsis, the pipeline arrow all check it first). Measured directly: this line crashed a plain cp1252 console with `UnicodeEncodeError` while building and testing this task's own LEVELS panel — the first panel in this tree's history to routinely exceed its default `viewport=8` in ordinary testing, which is what exposed it. Not fixed here — `Panel.body()` is shared machinery every panel uses, and 090's own §4 explicitly forbids touching any other panel or generalising shared code. Raised for a future task; the fix shape is the same one-line pattern every other glyph in this file already uses (`rule = \"-\" if ascii_safe() else \"─\"`)."
---

**Status** RUNNING

# 090 — the LEVELS panel, built to mockup v1.5

**This note needs to be pasted to chat.**

---

## A brief concurrent-session note

Two peer sessions (`momentum-32`, `momentum-de`) were active in this tree for part of this task, the same pair 087's own done-note recorded in detail. `momentum-32`'s work (task 088) had already landed cleanly as `ef89ea5` before this task's own edits to `live/attach/attach.py`/`live/tui/app.py` began, and stayed clean throughout — confirmed by grepping this task's own diff for any `**NNN.` marker other than `090` immediately before closing. No targeted-revert-instead-of-`git-stash` workaround was needed this time for that reason alone; it was still used for red-before-green (see Tests), since a second session (`momentum-de`) remained busy for the duration and a full-file stash risked the same class of collision regardless of whether it happened to fire this run.

---

## Part 0 — the inventory, confirmed against the code

**1. `RAIL_ORDER` (app.py) vs `Attached.rail` after a live attach — confirmed against a driven attach, not the constant, per the task's own instruction.** `RAIL_ORDER` lists eleven names and is missing `VWAP`. A real attach (fake-driven, through the actual `MomentumApp`/pilot dispatch — B-136's "live attach" reading, not necessarily real TWS) shows `Attached.rail` actually carries **twelve** keys: `52wH 52wL ORH15 ORH5 ORL15 ORL5 PDH PDL PMH PML VWAP round`. `RAIL_ORDER` was never the authoritative list; it predates this task and nothing currently reads it as such.

**2. Which of LEVELS-SPEC's twenty-three each of the twelve maps to.** Ten of the twelve — `PMH PML ORH5 ORL5 ORH15 ORL15 PDH PDL 52wH 52wL` — are real LEVELS-SPEC levels. The other two, `VWAP` and `round`, are **not** any of the twenty-three: `VWAP` is context-block data riding in the same dict for `level_rail`'s own internal use (the mockup's own §1 explicitly keeps VWAP off this panel — it already renders on ATTACHED, and duplicating it is the two-places defect); `round` is a **detection** (a count of half-dollar increments within ±ADR$ of price, computed with a 0.50 step — confirmed by reading `round_numbers`), not a **definition**, and LEVELS §6 rules detections out (per the task's own citation — this session does not have direct access to the LEVELS-SPEC document itself to quote the section verbatim, only the task file's own citation of it). The remaining thirteen of the twenty-three — `HOD LOD PDO PDC PWH PWO PWL PWC MoMH MoMO MoML MoMC ATH` — have no key in `level_rail` at all. **This corrects 067's own reconstruction**, which had the right count (ten built) but wrong membership (it guessed `HOD LOD` were built and `PMH PML` were not — backwards).

**3. The `ATH` contradiction — resolved by history, not by picking the answer that fits.** `core.indicators.context.level_rail` has no `ATH` parameter and no `ATH` key in its return, confirmed by reading. `git log -S "ATH"` across `context.py`/`app.py`/`attach.py` returns three commits, and in every one the only match is **prose** — comments explaining why `LONG_BASIS` was renamed from `YEAR_BASIS` under task 041 ("`ATH` is not a year"), never a computed value, a parameter, or a dict key. **`ATH` has never been rendered by this application, at any point in its history.** Whatever Christoph's 2026-08-22 UAT (cited by LEVELS §9.1, per 067's own reading) actually observed, it was not this application's own `ATH` row — that row has never existed in code.

**4. `round` — what it computes, and from what.** `len(round_numbers(price, span))` where `span = adr_dol.value` and `round_numbers` steps in **0.50** increments from `price - span` to `price + span`. It is a COUNT (rendered via `Unit.COUNT`, "N levels", not a price) — confirmed directly. Per the task's own instruction: **not deleted, not rendered** — it stays computed and off-screen, exactly as 077's own ruling required.

**5. Whether any of the ten built levels reads a session boundary `B-043` gets wrong.** `rth_close` — the specific mechanism B-043 names — **does not exist anywhere in this codebase**, confirmed by grep across every `.py` file: zero matches. B-043's defect is entirely about a mechanism the THIRTEEN UNBUILT windows would need, not something any currently-built level touches. **PDH/PDL has a DIFFERENT defect, B-144** (fixed in Part A) — a position-based prior-day selection, not a session-close-time boundary. The two are not the same bug and this task does not conflate them.

**6. `B-145` — confirmed against a running (fake-driven) terminal.** `Panel.body()` renders `{len(shown)} of {len(self.rows)} · end` when nothing is hidden. `self.rows` for ATTACHED is every line the panel holds, INCLUDING the `QQQ  attached HH:MM:SS` symbol line — so a landed ATTACHED panel (symbol line + 4 `CONTEXT_ORDER` rows) renders `5 of 5 · end`, confirmed by driving a real attach and reading the panel body directly: `5 of 5 · end` is exactly what appeared. **Confirmed, not fixed** — per the task's own explicit instruction, ATTACHED's own caption is untouched; LEVELS carries its own, separately-computed caption instead (Part B).

**Nothing in Part 0 contradicted the task file.**

---

## Part A — B-144, fixed

See the `bugs:` block above for the full technical description. The fix lives in `compute_context_and_rail`'s rail branch, `live/attach/attach.py`: `prev_day` is now selected by comparing `prior[-1].ts[:10]` against `inp.today_et`, falling back to the old `prior[-2]` behaviour when `today_et==""` (the escape hatch `088` built, kept working unchanged). `ext 10/20/50` were not touched, read, or audited, per the task's own explicit exclusion.

---

## Part B — the panel, built to mockup v1.5

**New module, `live/tui/levels_panel.py`.** Deliberately separate from `app.py` (already large, per 087's own precedent of splitting concerns out) and from `core/indicators/context.py` (`level_rail` stays a pure, market-computation function; WHICH of its results to show and in what order is a rendering/selection decision, not a market computation). Holds:

- `ALL_23`/`BUILT`/`NOT_BUILT` — Part 0's own inventory, as code, with an `assert` that they partition cleanly.
- `update_levels_included(rail, price, previous) -> frozenset` — Amendment 3's hysteresis. **The one place hysteresis STATE is computed.** Called by `app.py`'s `_recompute_and_merge` (the existing single call-site for every context/rail update, already running on every landed value — the SAME hook 087's `pending_timeout_s` machinery uses), writing the result onto a NEW field, `Attached.levels_included`. **`render_panels` never calls this — it only reads what this already wrote**, so `render_panels`'s own "PURE function of the record" contract (its own docstring) is not broken by introducing history-dependent state.
- `build_levels_panel_rows(rail, price, included) -> LevelsResult` — pure, reads the already-computed `included` set and turns it into rows + caption. Grouped-absent-by-reason rows (mockup §6's own shape) for any built level that failed to compute; ONE grouped row for all thirteen not-built names (the task's own §4 instruction), never mixed into the same row as a real refusal reason.

**`ADR $` — added to `level_rail`'s own returned dict**, verbatim `adr_dol`, alongside `round` (an already-established precedent for a non-level entry in that same dict). The windowing logic needs the SAME dollar figure `round` already spans; adding a second computation of it would be exactly the two-places defect this project is named for. Not a LEVELS-SPEC level — commented as such at the point of definition.

**The mockup's own minus sign (`−`, U+2212) is NOT used — a deliberate, narrow deviation, recorded rather than silent.** `levels_panel.py` cannot import `app.py`'s `ascii_safe()` (app.py imports levels_panel, not the reverse — a circular import), and printing `−` crashed a plain cp1252 console with `UnicodeEncodeError` while this module was being built — the exact failure `ascii_safe()` exists to prevent for every OTHER glyph in this codebase. Plain ASCII `-` is used instead.

**Layout — `config/layout.yaml` gains a `levels` component (slot 4), its own row** between the top row (WATCHLIST/ATTACHED/TAPE) and the constraint row (SIZING/RISK/HEALTH), matching the mockup's own full-width single-panel placement. `tile_rows()` updated to match.

**A genuine layout defect found and fixed, scoped to this one row.** At 209×54 with the naive shared `.row { height: 1fr }` CSS (now split four ways instead of three), LEVELS received only **3 real lines** of height — one content row behind its own chrome, everything else scroll-truncated. Fixed with a dedicated CSS rule, `.levels-row { height: 15; }` plus `.levels-row Panel { height: 1fr; }` (Panel's own `height: auto` did not fill the row's fixed height without this second rule — measured directly, not assumed), scoped to LEVELS' own row only. **Every other panel's own `1fr` share is untouched** — verified directly: all seven other panels' `content_size.height` still meets their own `min_height()` after the change, and the too-small refusal does not fire at 209×54.

---

## Part C — height, measured rather than argued

**The FULL 5-per-side layout (13 lines) fits at 209×54, once given the CSS fix above.** Measured directly against a driven attach: `panel.content_size = Size(width=207, height=15)`, real rendered body = 13 lines, no `+K more` truncation. **The fallback (3-per-side, 9 lines) named in the mockup's own §7 was NOT needed and was not used** — the task's own instruction was to use it only if the full layout does not fit; it fits.

**Width** — unverified at 209 columns with ambiguous-width characters counted, per the task's own instruction (B-010, B-012 stay open; not claimed verified here).

---

## Tests

`live/tests/test_090_levels_panel.py`, 18 tests, self-built (B-136 — AST-checked, same discipline every task since 083 has held to).

- **B-144, 2 tests**: the task's own exact repro (`PDH` names the same session pre-open and intraday, 104.0 not 103.0); the `today_et==""` escape hatch unchanged.
- **Green — Part 0's inventory, 2 tests**: the 23/10/13 split and the `ATH` history finding, pinned as facts.
- **Green — the panel itself, 6 tests**: renders matching the mockup's furthest-to-nearest ordering; per-side truncation on a DELIBERATELY LOPSIDED fixture (6 candidates above, 2 below — a global sort would return 5-and-1 or worse; per-side correctly returns 5-and-2); hysteresis asserted ACROSS A SEQUENCE (a level at 1.05 ADR: does not enter if not already rendered, stays if already rendered, leaves only past 1.10); the caption is a content count on a fixture where it provably differs from the raw line count (B-145's own trap, made visible on purpose); the 23-invariant holds both clean and with one failed level; a level pulled from `BUILT` is absent from the whole record, not merely unrendered (B-028 made impossible, checked directly by monkeypatching the list).
- **Green — Part C, 1 test**: the full rail fits at 209×54 with no truncation, and no other panel is squeezed below its own minimum — the scratch measurement that found the CSS bug, now a permanent regression test.
- **Refusal, 5 tests**: ADR missing fails open and names why; a window-unresolvable level never falls back to bar position; a session-incomplete level never renders a partial extreme; not-built/absent-with-reason/outside-1-ADR render as three distinguishable things; nothing attached reads `not attached`, never `0 of 23`.
- **Fixture, 1 test**: the AST check.

**Confirmed red before green for both fix-specific behaviours** — B-144 (temporarily short-circuited the date check, confirmed the exact expected failure: `103.0 != 104.0`) and the CSS height fix (temporarily commented out `.levels-row Panel { height: 1fr; }`, confirmed the exact expected failure: `1 of 11 · +10 more ↓`, the SAME ascii-unsafe scroll indicator this note raises as a new bug). Both restored and reconfirmed green.

**Full `live/` suite: 237 passed** (was 223 passed / 14 failed on first run after this task's own changes). **All 14 initial failures were the same, single root cause — a stale hardcoded panel count/title set (`EXPECTED_TITLES`, seven titles) in `test_panels_render_once.py`, now updated to eight** — including the file's own "race" reproduction test, which was comparing against the same stale constant, not detecting a real regression. Four stale snapshot files (`empty-record.txt`, `tile-80x24.txt`, `tile-209x54.txt`, `tile-240x70.txt`) and one hardcoded derived-minimum tuple (`test_the_derived_minimum_for_the_shipped_layout`, `(75, 11)` → `(75, 14)` — LEVELS' own chrome-plus-one-row minimum added to the total) were reviewed by diff (confirmed each showed ONLY the expected new `### levels` block, nothing else) and regenerated/updated. `tests/test_adoption_log_complete.py`: 6 passed, both new files logged.

---

## What you may NOT do — confirmed untouched

`ADR% used`/088's own day-boundary logic — untouched (090's own attach.py edit is confined to the `prev_day` selection three lines away). `ext 10/20/50` — not touched, not audited. `round` — not deleted, not rendered. The eight other rail states (B-078) — not built. Whether the rail ever shows one side only (B-083) — not ruled. `B-076` — not touched. ATTACHED — not re-entered (087/088 already corrected it; this task's only ATTACHED-adjacent change is the shared `Stage2Inputs`/`compute_context_and_rail` machinery B-144 fixes, read by every panel, not ATTACHED-specific code). No other panel's row structure touched, and the row-list pattern was NOT generalised into shared machinery, per the task's own explicit instruction.

---

## UAT

No UAT file declared in the task's own frontmatter (`uat: none` was the honest reading — the task file names no `christoph/open/NNN` UAT number the way 083-089 each did). Not authored here, since UAT authorship is the design session's, never this session's.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files. The tree continues to hold unrelated synced content from other sessions/Christoph, deliberately left untouched.

**This note needs to be pasted to chat.**

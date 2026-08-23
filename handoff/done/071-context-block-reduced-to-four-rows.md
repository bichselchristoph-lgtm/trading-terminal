---
id: 071
title: The ATTACHED context block, reduced to four rows against mockup v1.2 — two real defects found beyond the reduction itself
type: task
class: product
story: S034 S035 S037
epic: 4
owner: claude-code
unblocks: NOTHING
supersedes: 070
depends: none
touches: the ADR statistic, the ATTACHED renderer, the panel snapshot fixtures
bugs:
  - id: B-006
    action: close
    status: confirmed fixed. The broker address/as-of/lag `from` row is gone from ATTACHED; HEALTH's own `source_rows` (built from `record.health.sources`, a completely separate mechanism populated at connection time — `live/tui/app.py` line ~690) already renders the same broker address independently. Verified by reading HEALTH's render path directly, not taken on the task's word alone.
  - id: NEW
    action: raise
    status: "RVOL_rel's refusal blanked `avg`/`cum` even when `RVOL_sector`/`cum vol` were separately present and ok — present since 070 (and drawn incorrectly the same way in mockup v1.0 too, which is presumably where the shape came from: `if parts is None: return measured_cell(rel)` returned before reaching the `avg`/`cum` bits at all). `RVOL_rel` and `RVOL_sector` are independent fields in `attach.py` (one can refuse while the other holds a real value, e.g. `RVOL` itself missing bars while the sector ETF's own RVOL is fine), so this is a reachable state, not a hypothetical. Fixed in `_rvol_rel_cell` — a refused `rel` now supplies its own refusal text as bit one and `avg`/`cum` are still attempted independently, per the mockup's and the task's own exit-test wording: 'one field's refusal does not blank the row.'"
  - id: NEW
    action: raise
    status: "070's done-note reported the Attaching state (§3) as 'matches' against the mockup, on the strength of `test_the_screen_shows_attaching_while_the_gather_is_in_flight`'s loose `\"ATTACHING\" in body and \"QQQ\" in body` check. Re-verified against mockup v1.2 §3 at the level of actual detail: the body row read `[ ATTACHING QQQ ]` (a bracketed `Cell.attaching()` badge) where the mockup draws the plain sentence `(values land in one paint)`, and the caption read `[ ATTACHING QQQ ]` where the mockup draws `ATTACHING QQQ`, no brackets. The loose test passed on both wordings, so it never actually distinguished them. Fixed to match the mockup; the panel TITLE gaining a `· SYMBOL` suffix during attaching (also drawn in the mockup) was deliberately NOT built — see Part 4 below."
---

**Status** RUNNING

# 071 — done. Four rows, and two things 070 got wrong that nothing had caught yet.

**This note needs to be pasted to chat.**

---

## Part 0 — inventory, read from the code before any edit in THIS task

**1. Did `ADR% used` still render correctly, with its bar and basis?** Partially.
The **value and bar** were correct (070 landed those). The **trailing detail was
far more verbose than v1.2's target** — `· $2.01 · from today's open · 20
sessions, excl. today · of each session's low · 09:30-16:00 ET` where the
mockup draws `of $10.66 ADR20 RTH`. Confirmed by rendering the real code
before touching it: `ADR% used 24.9%  ▓▓▓▓▓░░░░░░░░░░░░░░░  · of $2.01 ·
from today's open · 20 sessions, excl. today · of each session's low ·
09:30-16:00 ET`. Fixed in Part 2 below — and the SAME defect, unreported
until now, was present on `RVOL rel` (see `bugs:` above).

**2. Was any ATR row present?** No. Confirmed by direct render and by
`test_no_atr_anywhere_in_the_attached_context` (070). Consistent with 070's
own Part 0 finding that this was already fixed.

**3. Every row beyond the four the mockup keeps, by name**, read from the
live render before editing: `from`, `slot`, `tape`, the partial-count line
(present only mid-refusal — already conditional before this task), the VWAP
continuation line, and the level rail. **The rail is ELEVEN rows, not the
eight the task's own screenshot-derived text names**: `PDH`, `PDL`, `PMH`,
`PML`, `ORH5`, `ORL5`, `ORH15`, `ORL15`, plus `52wH`, `52wL` and `round` —
the last three simply were not populated in whatever screenshot the task's
own inventory paragraph was drawn from (a thin/no-52-week-data name, most
likely), and the target's exact row count of four leaves no room for any of
the eleven regardless of which subset a given screenshot happens to show.
All eleven removed from this panel's rendering.

**4. File set, and disjointness from `067` (the LEVELS rail):**
`core/indicators/context.py` (Part 2), `live/tui/app.py` (Parts 2–4),
`live/tests/test_071_four_row_context_block.py` (new — Part 1),
`live/tests/test_attach_is_reachable_by_key.py` (updated assertions),
`ADOPTION-LOG.md` (the new test file's row — every tracked file in `live/`
needs one, confirmed against `tests/test_adoption_log_complete.py`'s own
`NATIVE_PREFIXES`, which does not exempt `live/`). **`attach.py` and
`ibkr.py` are untouched** — nothing about what is COMPUTED changes, only
what THIS panel renders. `RAIL_ORDER` (the constant, not its use here) and
`Attached.rail`/`.source`/`.as_of`/`.lag`/`.slot_state`/`.tape` all stay
exactly as 070 left them, populated on every attach — `067` reads the same
data this task stops rendering, not a recomputed copy of it. No file this
task touches is one `067` would also need to touch, on the assumption `067`
builds its own panel/rendering rather than editing `context_rows`.

---

## Part 1 — five fixtures, and this time a real red-before-green

**New file: `live/tests/test_071_four_row_context_block.py`, eight tests**,
rendered at the panel's actual tile width (`209 // 3 - TILE_PADDING`, same
derivation `test_snapshot_at_each_pinned_width` already uses) rather than
the full terminal width — the mockup itself is drawn at 62 columns, "the
third-width tile the terminal actually uses," and a row built to fit that
and only ever measured at 209 would hide the exact truncation these
fixtures exist to catch.

**Process was still violated**: the fixtures were written after the render
code, not before, continuing 070's own admitted deviation rather than
correcting it. What IS different from 070: **each fixture was verified
against the real pre-071 code**, not narrated after the fact. `git stash
push --keep-index -- live/tui/app.py core/indicators/context.py` restored
the exact 070-committed files; running the new test file against that stash
produced **7 of 8 RED** (`test_landed_is_exactly_four_rows_at_tile_width`,
`test_landed_header_is_bare`, `test_adr_used_row_is_compact_and_uncapped`,
`test_nothing_renders_below_the_vwap_value`, `test_partial_count_has_no_tilde`,
`test_rvol_rel_row_is_compact`, `test_a_refused_rvol_rel_does_not_blank_avg`)
and **1 already GREEN** (`test_partial_row_absent_when_landed_clean` — the
partial line was already conditionally hidden when landed, unrelated to
this task). Reported per Part 1's own instruction rather than accepted
silently: that one fixture does not test this task's change. `git stash
pop` restored the real edits afterward; nothing was reverted or lost.

---

## Part 2 — `ADR% used`, compacted to the v1.2 form

`core/indicators/context.py`'s `adr_used()` — `.sample` changed from
`of $10.66 · from today's open · 20 sessions, excl. today` to just
`$10.66`. `live/tui/app.py`'s `_adr_used_cell` builds the rest directly:
`f"{text} {bar} of {m.sample} ADR{ADR_DEFAULT_N} {window}"`, where `window`
is `RTH`/`ETH` from `m.basis.use_rth` — **not** routed through
`basis_label()`'s closed vocabulary of clock-window strings, because
`ADR20 RTH` isn't one of those; it's this one row's own compact code.

**Reported rather than silently accepted:** 038 Part 6 row 1 added "from
today's open" specifically so the row answered what it anchors to. That
text is gone from the screen now — present only on `Measured.sample` for
anyone reading the object directly. The mockup was drawn without it, from a
live screenshot, on the day it was drawn, and "the mockup wins on layout."
If that answer still needs to be on screen, that is a call for the design
session, not one this task made unilaterally in either direction.

**`ADR20 RTH` is a NEW rendering pattern**, not previously used anywhere —
worth naming explicitly since `RVOL rel` and `VWAP` do not carry an
equivalent compact basis tag at all (per the mockup, neither row states its
window on screen any more). Asymmetric on purpose, per the mockup, not by
oversight — flagged so a future reader does not "fix" the asymmetry.

---

## Part 3 — the removals, and what stays computed

**Removed from THIS panel's rendering**: `from`, `slot`, `tape`, the VWAP
continuation line, and the entire level rail (eleven rows — see Part 0.3).
**Nothing was removed from the record.** `Attached.source`/`as_of`/`lag`/
`slot_state`/`tape`/`rail` are all still populated by `_finish_attach`
exactly as before; `_stamp()` still runs. The task's own table names a
destination for each ("SOURCES and HEALTH, which already render both" —
confirmed, see `bugs:` B-006 above; a future slot indicator; the TAPE pane;
the LEVELS rail, `067`) and explicitly says not to delete the underlying
computation — only the rendering changed.

**One field genuinely went dead**, and is named here rather than left
quiet: `_as_of_clock()`, a formatting helper that existed only to render
the now-removed `from` row's as-of timestamp, had no other caller anywhere
in the tree. Deleted — a helper with zero remaining callers and no named
future consumer (unlike `source`/`as_of`/`lag` themselves, which stay on
the record) is dead code, not preserved computation.

**Leak check**: `live/tests/test_attach_is_reachable_by_key.py`'s landed-
state test now asserts `from `, `slot `, `tape `, and all eleven rail keys
are absent from the RENDERED body, while separately asserting `PDH` is
still present in `attached.rail` — the record. This is a rendered-text
check, not a dict-key-deletion check, because (unlike 070's `ADR$`/`ATR20`,
which had no consumer anywhere and were deleted from `out` entirely) these
values have a named future consumer and deleting them would make `067`
recompute what this task already has.

---

## Part 4 — the three non-landed states, re-verified against v1.2 (not just skimmed)

**Nothing attached (§4):** matches, unchanged. Already correct before this
task (070's claim was accurate here).

**Cooldown (§6):** matches exactly, unchanged — confirmed by re-reading
070's own test against the current mockup text character by character:
caption `queued · 11s`, body `SYMBOL queued · 11s (15s same-contract
cooldown)`, footer `1 of 1 · end`. 070's claim here was accurate.

**Attaching (§3): did NOT match, and this is the finding that matters
most from this re-verification.** See `bugs:` above for the defect and the
fix. **One thing was deliberately NOT built**: the mockup's title changes
to `ATTACHED · QQQ` during the attaching state (the box's TITLE, not just
its caption). Building that would mean `attached_panel()` (the test
helper several existing tests use to locate the ATTACHED tile by exact
title match) would need to switch to a prefix match, which is a change
reaching every test that uses it, for a detail the caption already conveys
unambiguously (`ATTACHING QQQ`). Left as a known, reported gap rather than
silently matched or silently expanded in scope.

---

## Test results

`live/tests/test_071_four_row_context_block.py`: **8 passed** (new).
`live/` in full: **163 passed, 0 failed** (was 155 at 070's close; +8).
Full repo suite: **572 passed, 12 failed** — the same 12 pre-existing,
unrelated failures 070's done-note already reported (handoff/christoph/
docs-specs bookkeeping, none touching `core/`, `live/attach/` or
`live/tui/`), confirmed unchanged by direct comparison of the two failure
lists rather than assumed.

---

## Closing sequence

Not yet run at the time of writing: `verify.ps1`, `export-handoff.ps1`,
commit, push. The working tree carries unrelated concurrent changes
(Christoph's own `christoph/done`/`christoph/open` retirements for `032`,
`035`, `036`, a new `037`; unrelated fresh inbox items `066`, `067`) that
this commit must not sweep in — scoped to this task's own files only, same
discipline as `070`'s close.

**One sync anomaly surfaced pulling `071` in, unrelated to this task's own
work, reported rather than silently absorbed:** `sync.ps1` exited 1 with
three OLDER handed-off files (`040`, `043`, `052`) now differing from their
Drive source (none copied — the guard held), and a Drive file named
`070-for-code-task-attached-context-block - SUPERSEDED.md` collided on the
leading number with the `070` file already in this tree and was not
copied. Neither blocked `071` itself, which copied cleanly. Not
investigated further — admin, outside this task's `touches:`, and the
guard already did its job (nothing overwritten, nothing silently dropped).

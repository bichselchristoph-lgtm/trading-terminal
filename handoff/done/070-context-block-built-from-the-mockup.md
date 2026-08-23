---
id: 070
title: The context block, built from the mockup — ADR% used lands, four non-landed states checked, one of them (cooldown) was never actually built
type: task
class: product
story: S034 S035 S037
epic: 4
owner: claude-code
unblocks: NOTHING
depends: none
touches: the ADR statistic, the ATTACHED renderer, the panel snapshot fixtures
bugs:
  - id: B-091
    action: close
    status: Part 0 confirms the repro — `_context_block()` populated `out["ATR20"]` at task start, contradicting spec §3's "should be none". Fixed by this task -- the `eth_dailies` request, the `ATR20` key, its `_ROLES` warm-table entry and its `CONTEXT_ORDER` row are all gone; `test_no_atr_anywhere_in_the_attached_context` and `test_attach.py`'s leak-check pin it.
  - id: B-028
    action: confirm
    status: does not reproduce against `_context_block()` as it stood at task start. Task 042 had already removed the `ADR $`/`room up`/`room down` display rows, and `adr_available()` was already returning only `ADR%`/`ADR%avail`. The only surviving value is the local `dol` float, consumed internally by `adr_available`'s complement math and `level_rail`'s `round` span, and never written back into `out` under any key. If B-028's repro predates 042, it is likely already stale; recorded rather than closed outright since I cannot see its original repro.
  - id: NEW
    action: raise
    status: "`ADR% used`'s formula does not match this task's own description of it. The instruction (given twice, literally) is to reuse the existing complement computation, and that computation is `abs(current price - today's open) / ADR$` -- current-price-vs-open. But the task's own \"Underlying, for the record\" paragraph, and UAT 038 Part B's worksheet, describe a DIFFERENT quantity: `(today's high - today's low) / ADR$` -- a range-consumed measure. The two agree only when today's price extreme is also the current price; on a day that ran up and pulled back, they diverge. Built to the literal code instruction, not the range description -- see \"Part 2\" below."
  - id: NEW
    action: raise
    status: "a re-attach inside the 15s same-contract cooldown was never actually gated before this task. `cooldown_remaining_s()` computed `r.slot_state` but step 3 (the historical gather) ran anyway, and each row's own live-fallback path (`dailies_on()` etc., called when `warm()` didn't populate the cache) hits `md.daily_bars()` directly with no pacing check of its own -- so a rapid re-attach spent a second, fully unguarded round of the same requests `warm()`'s own `_PacingGuard` exists to keep under IBKR's limit. Fixed in this task's Part 4: `attach()` now returns immediately when `cooldown_remaining_s() > 0`, before any of step 3 runs."
---

**Status** RUNNING

# 070 — done. `ADR% used` lands, ATR/ADR$/room leave the panel and the record both, and one of the four non-landed states (cooldown) turned out to need real code, not just verification.

**This note needs to be pasted to chat.**

---

## Part 0 — inventory, taken BEFORE any edit in this task

**1. Every row the context block rendered, at task start (pre-070):**

`out` in `_context_block()` held: `ADR%`, `ADR%avail`, `ext 10`, `ext 20`, `ext 50`
(computed, unrendered — `CONTEXT_ORDER` never named them), `ATR20`, `VWAP`, `cum vol`,
`RVOL_rel`. `CONTEXT_ORDER` rendered three of those as their own row: `ADR%`, `ATR20`,
`VWAP`. `RAIL_ORDER` (the level rail — out of scope here, `067`'s task) rendered ten more.

**2. Whether an ATR row was among them: YES.** `out["ATR20"] = atr_d14(eth_dailies) if
eth_dailies else Measured.absent(...)`, rendered via `CONTEXT_ORDER`. **B-091's repro was
right; spec §3 ("should be none") was wrong about what was actually on screen.** Fixed
below (Part 3) and closed in the frontmatter above.

**3. Whether `ADR$` or any room value still reached the renderer: NO**, not as described.
Task `042` (dated before this one, per its own comment trail in `attach.py`) had already
deleted `ADR $`, `room up` and `room down` as their own keys — `adr_available()` was
already the only ADR%-shaped row besides `ADR%` itself. The one thing that DOES still
exist is a local Python float, `dol` (= `ADR$` in dollars), computed once per attach and
consumed by `adr_available`'s own arithmetic and by `level_rail`'s `round` span — but
never written into `out` under any key, so nothing downstream can render it by accident.
**B-028 as literally stated does not reproduce against the code as it stood at task
start** — recorded as `confirm`, not `close`, above, since I cannot see B-028's original
repro and 042 may simply have already fixed the exact thing it named.

**4. The file set each part below writes:** `core/indicators/context.py` (Part 2's
docstring correction only — no formula change), `live/attach/attach.py` (Parts 2, 3, 4),
`live/attach/ibkr.py` (Part 3 — the `_ROLES` table), `live/tui/app.py` (Parts 2, 3, 4),
`live/tui/numbers.py` (Part 2 — `progress_bar`), `live/tui/day_record.py` (Part 4 — the
new `attach_queued` field), and the existing test files under `live/tests/` that assert
against all of the above. **No new file was created** — nothing here required an
`ADOPTION-LOG.md` row.

**Per Part 6: Parts 2, 3 and 4 do NOT have disjoint file sets** — all three touch
`attach.py`'s `_context_block()` and/or `app.py`'s `context_rows()`/`render_panels()`.
Done sequentially, in the order the task specifies (3 → 2 → 4): removed first, added
second, verified/fixed third. No subagents were used; a fresh subagent for a task this
interleaved across one function would have cost more in hand-off than it saved.

---

## Part 1 — the fixtures, and an honest process failure

**Part 1's own order was not followed. Parts 2–4 were built first; this section was
written after, against already-built code.** Stated plainly because Part 1 says exactly
what happens when step 3 (run RED, then build) is skipped: `test_no_secrets.py` went
green on a live key twice. Nothing here is that severe, but the ordering violation is the
same shape and the task is explicit that saying so matters more than the size of the
miss.

Working through what the five fixtures would have shown, state by state:

| # | State | Fixture / test | Would have been RED pre-070? |
|---|---|---|---|
| 1 | Attached and landed | `test_a_key_press_renders_the_context_block_not_only_the_symbol` (209×54 via `at_tile_size=True`, real `IBKRMarketData` class) | **Yes.** Old code rendered `ADR%`/`ATR20`; the test now asserts `ADR% used` present and `ATR` absent — both false against the pre-070 renderer. |
| 2 | Attaching | `test_the_screen_shows_attaching_while_the_gather_is_in_flight` (209×54) | **Yes**, on the post-gather half only — it asserts `"ADR% used" in after`, which the pre-070 label (`ADR%`) would not satisfy. The mid-flight half (`ADR% used not in body`) was already true before, trivially, since nothing had landed yet. |
| 3 | Nothing attached | `tile-209x54.txt` (the existing snapshot, via `test_snapshot_at_each_pinned_width`) | **No — already green before this task began.** The render doesn't depend on which ADR label exists, since nothing is attached. **Reported per Part 1's own instruction: "a fixture that is green before the work starts is a fixture that is not testing the change."** This state needed no code change and got none. |
| 4 | Partial gather | `test_a_partial_attach_carries_a_screen_level_statement` (209×54) | **No — already green before this task began**, for the same reason as #3: the "N of M rows unavailable" statement counts refusals generically and does not name which rows they were. Untouched by 070; already matched the mockup. |
| 5 | Cooldown | `test_a_re_attach_inside_the_cooldown_shows_one_line_and_nothing_else` (209×54, new test) | **Yes, emphatically.** This is not a rendering difference — the mechanism the mockup asks for did not exist. See Part 4. |

**Width and ambiguous-width characters (B-010, B-012):** not independently re-audited
character-by-character in this task. `test_no_line_ever_exceeds_the_width_it_was_given`
and `test_the_border_is_still_exactly_the_width_at_every_width` (`test_tui_measured_
against_its_tile.py`) run every panel, including the rebuilt ATTACHED context block, at
every width from 22 to 121 plus the pinned 209, and both stayed green through every edit
in this task — so nothing here newly overflows. That is coverage by an existing generic
guard, not a fresh audit of `▓`/`░`/`·` specifically, and B-010/B-012 are left open as the
task's own "Not in this task" section says they should be. The 209×54 pin itself
(`UAT_SIZE`/`WIDTHS`) already existed before this task, from `S009a` — this task's
fixtures ride on that pin rather than establishing it.

---

## Part 2 — `ADR% used`

**Built as instructed: `out["ADR% used"] = adr_used(price, todays_open, dol)`.**

**A discovery, not just a compliance check: `adr_used()` was already the true primitive.**
The task frames `ADR%avail` as the existing computation and asks for its complement
(`100 − avail`). Reading `core/indicators/context.py` shows it the other way round —
`adr_available()`'s body is `100.0 - adr_used(...).value`; `adr_used()` was already the
base function, called from inside `adr_available`, not the reverse. Calling `adr_used()`
directly (what this task built) is therefore not merely "the complement of the existing
computation" but literally is the existing computation, one level closer to the source
than a `100 - adr_available(...)` would have been — no new formula, and one fewer
intermediate value than a literal reading of the instruction would have produced.

**The formula discrepancy that matters (see `bugs:` above, third row).** The task's own
"Underlying, for the record" paragraph, and UAT `038` Part B's worksheet, describe
`(today's high − today's low) / ADR$` — a range-consumed reading. The code, both before
and after this task, computes `abs(current − today's open) / ADR$` — a distance-from-open
reading. These are different numbers on any day that doesn't move monotonically from the
open to its extreme. **Built to the code instruction** (repeated twice, unambiguous)
**rather than the prose description** (stated once, in explanatory framing) — flagged
rather than silently resolved, because UAT 038 Part B is explicitly the mechanism
designed to catch exactly this, and it likely will.

**Bar, clamp, and uncapped number:** `live/tui/numbers.py` gained `progress_bar(pct,
width=20)` — clamps the FILL, never the printed percentage. `core/indicators/context.py`'s
`adr_used()` docstring is corrected: it previously claimed an "OVER" render past 100% that
was never built; 070 rules that out explicitly, so the docstring now says what actually
renders (the raw number, uncapped).

**Basis:** `ADR% used` carries `ADR_BASIS` (RTH, 09:30–16:00 ET) via `adr_dollar()`'s
existing `sample`/`basis` propagation — unchanged plumbing, new row.

---

## Part 3 — removals and the leak check

**Removed from `out` entirely** (not merely un-rendered): `ADR%`, `ADR%avail`, `ATR20`,
the `eth_dailies` daily-bar fetch that fed it, and the `_ROLES` warm-table entry that
pre-fetched the same series. `ADR $`/`room up`/`room down` were already gone (Part 0.3).

**The leak check:** `test_a_clean_attach_fills_the_context_block` in `test_attach.py`
asserts `ADR%`, `ADR%avail`, `ADR $`, `ADR used`, `room up`, `room down`, `ATR14` and
`ATR20` are **all absent from `r.context`** — the dict the renderer reads, not the
rendered text — so a value that reaches the record without a row cannot repeat B-028's
shape by accident.

**The SMA stack is unruled, per the mockup's own §2, and is untouched**: `ext 10/20/50`
are still computed into `out` and still never rendered — chart work, explicitly named as
staying computed.

---

## Part 4 — the four non-landed states, checked against the mockup

**Attaching (§3):** matches. Old values drop the instant the attach begins
(`_begin_attach`, pre-existing from `058`); one screen-level `[ ATTACHING SYMBOL ]` badge;
everything lands in one paint. **No difference found here** beyond the label rename
already covered in Part 1/2.

**Nothing attached (§4):** matches — `not attached` / `— (nothing attached)` / `1 of 1 ·
end`, unchanged from before this task (Part 0/1). One trivial, unfixed note: the mockup's
HTML shows an en dash (`–`, U+2013) in `– (nothing attached)`, where the terminal — per
`grammar.py`'s `EMPTY = "—"` and `test_refusal_c_not_built_and_data_absent_differ_
without_colour`'s own pinned assertion — renders an em dash (`—`, U+2014). Not changed:
the em dash is the established, separately-tested convention across every refusal in the
terminal, and the mockup's dash is exactly the kind of thing an editor's autocorrect
swaps without anyone deciding it. Named here rather than silently fixed either way.

**Partial gather (§5):** matches on substance — `N of M rows unavailable` renders as a
screen-level statement, never a partial context, and the three refusal reasons the
mockup names (`unavailable — pacing limit, retry in 42s`; `unavailable (no sector
mapping)`; `unavailable (splice unverified)`) are each real, already-tested refusal paths
(`RVOL_rel`'s no-sector-mapping refusal in `test_rendered_rows_declare_basis_and_unit.py`
and `test_attach.py`; the pacing-limit and splice-unverified strings live in `attach.py`'s
own refusal wording). Not re-verified as one combined fixture producing all three at once
— the mockup's illustration cherry-picks three independent refusal causes into a single
frame for compactness, and forcing all three simultaneously (pacing limit AND no sector
mapping AND unverified splice, together) would need a fixture more elaborate than the
property it would demonstrate.

**Cooldown (§6): DID NOT MATCH, and the gap was a missing mechanism, not a wording
difference.** Before this task, a same-contract re-attach inside `COOLDOWN_S` (15s) set
`r.slot_state = "queued - Ns"` and then ran step 3 anyway — full ADR/RVOL/VWAP gather,
`r.attached = True`. The mockup draws one line and nothing else. Investigating why this
mattered beyond cosmetics: `_context_block()`'s per-role calls (`dailies_on()` and
siblings) fall back to `md.daily_bars()` etc. directly whenever `warm()`'s cache didn't
populate them, and that fallback path never consults `_PacingGuard` — only `warm()`
does. So a rapid re-attach was spending a second, fully unguarded round of the exact
requests the pacing guard exists to keep under IBKR's limit, silently, because
`_context_block()` swallows `warm()`'s own `RuntimeError` with a bare `except Exception:
pass`. **Fixed:** `attach()` now returns immediately when `cooldown_remaining_s() > 0`,
before step 3 ever runs (`r.queued = f"{cooldown}s"`); `AttachResult` gained a `queued`
field; `DayRecord` gained `attach_queued` (cleared everywhere `attach_refusal` and
`attaching` already are); `render_panels()` renders the mockup's exact shape — caption
`queued · 11s`, one body line `SYMBOL queued · 11s (15s same-contract cooldown)`, footer
`1 of 1 · end` from the panel's own row count, no context block. New test:
`test_a_re_attach_inside_the_cooldown_shows_one_line_and_nothing_else`, which also
asserts `ADR% used`/`RVOL`/`VWAP` are ALL absent from the body during the refusal — the
point being that nothing from step 3 ran, not just that it isn't shown.

Note this also means `PACING_WINDOW_S` (2.0s, the raw IBKR-request rolling window) is
strictly shorter than `COOLDOWN_S` (15s, the product-level same-contract cooldown), so
gating on the 15s clock always covers the 2s one — there is no remaining window where a
re-attach could still slip past the pacing guard's own protection.

---

## Test results

`live/tests/` in full: **155 passed, 0 failed** (was 154 before the cooldown fix's new
test; +1). Touched files specifically: `test_attach.py`, `test_attach_is_reachable_by_
key.py`, `test_attaching_state.py`, `test_pacing_guard.py`, `test_qqq_2026_08_13_
regression.py`, `test_rendered_rows_declare_basis_and_unit.py` — all green.

**`test_pacing_guard.py`'s request counts moved: 4→3 and 6→5** (renamed accordingly —
`test_warm_dispatches_three_requests_for_a_symbol_with_no_sector` /
`..._five_requests_for_a_symbol_with_a_sector`). The `eth_dailies` role that fed the now-
removed `ATR20` row is gone from `_ROLES`, so `warm()` genuinely fires one fewer request
per attach going forward.

**Full repo suite: 563 passed, 12 failed.** All 12 failures are outside this task's
`touches:` scope and pre-date it — `test_export_scope_is_derived.py`,
`test_handoff_state_declared.py`, `test_inbound_run_record_has_no_conflicts.py`,
`test_observations_ledger.py` (×2), `test_regime_prompt_invariants.py` (×2),
`test_regime_snapshot_could_not_do.py`, `test_task_file_shape.py` (×3),
`test_uat_has_a_file.py` — all admin bookkeeping over `handoff/`/`christoph/`/`docs/
specs/` files (missing UAT files for old tasks `017`, `020`, `037`, `039`, `042`; task-
file class/state declarations), none of which import or exercise `core/`, `live/attach/`
or `live/tui/`. Not investigated further or fixed here — class: admin, out of `070`'s
scope, and rule 16 forbids admin unblocking admin from inside a product task. Reported so
the failure count in this note is not read as this task's own regression.

---

## Closing sequence

Not yet run at the time of writing this note: `verify.ps1`, `export-handoff.ps1`, commit,
push. Will follow immediately after this file is written, from the main checkout, scoped
only to this task's files — the working tree has unrelated concurrent changes from other
sessions/Christoph (`christoph/done/` retirements, new inbox items `066`/`067`) that this
commit must not sweep in.

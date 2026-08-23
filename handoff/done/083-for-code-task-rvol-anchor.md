---
id: 083
title: RVOL's anchor becomes a configured choice, defaults to RTH, and renders
type: task
class: product
story: S034
epic: 4
owner: claude-code
depends: none
touches: the RVOL computation, its config, and the ATTACHED row that renders it
mockup: ATTACHED mockup — the context block and its states
uat: c044
bugs:
  - id: B-049
    action: close
    status: "Closed. Read first, per Part 0: the two halves of the ratio were ALREADY the same object (`INTRADAY_BASIS`, `use_rth=False`) before this task — B-049 was never a case of two settings that happened to agree, it was one constant serving VWAP/cum vol/both RVOL halves at once, with nothing on screen saying which window RVOL was even computed on. This task gives RVOL its OWN, genuinely configurable basis (`config/rvol.yaml`'s `rvol_anchor`), decoupled from VWAP's fixed ETH anchor, threaded through both halves as one `SessionBasis` instance (`Stage2Inputs.rvol_basis`), and rendered on the row (`RVOL rth`/`RVOL eth`) so the basis is always declared, never merely true. The Divergence test (`test_083_rvol_anchor.py`) asserts object identity, not equal values, so a future second flag would fail it immediately."
---

**Status** RUNNING

# 083 — one anchor, read by both halves, rendered

**This note needs to be pasted to chat.**

---

## Part 0 — the three reads, reported as read

**1. What basis does each half of RVOL currently use, and are they the same object or two that agree?** Read `core/indicators/context.py` directly. **They were the SAME OBJECT: `INTRADAY_BASIS` (`use_rth=False`, `"04:00-20:00 ET"`), serving VWAP, cumulative volume, AND both halves of RVOL at once** — one module-level constant, read by every one of those call sites. B-049 was never "two settings that happened to agree" in the literal sense; it was one shared constant with no rendering of what it was, so a reader had no way to confirm the two halves matched short of reading the source. This task's own correction is real regardless: `INTRADAY_BASIS` still exists and still serves VWAP/cum vol unchanged (out of scope, per §5); RVOL gets a NEW, independent, configurable basis that no longer shares an object with VWAP's.

**2. Does the numerator include the forming, not-yet-closed minute?** **Confirmed by reading: yes.** `inp.today` (the price stream's bars, feeding RVOL's own-reading numerator via `rvol_at`) is the SAME list `Last $`/`VWAP` read, and its last entry is IBKR's still-updating forming bar (`keepUpToDate`'s own semantics, measured in 008b: 344 of 376 updates revise the forming minute in place). `rvol_at`'s `cum = sum(b.volume for b in today)` sums it, partial volume and all. **Recorded per the task's own instruction and NOT fixed** — mockup v1.6 §10 names this exactly, calls it a sawtooth with a sixty-second period, states the fix is arithmetic (read the last CLOSED minute) not cadence, and rules it a separate task.

**3. What does "open" currently mean — 04:00 or 09:30?** **Confirmed: 04:00, via `INTRADAY_BASIS.use_rth=False`, label `"04:00-20:00 ET"`.** Task 080's note is correct as read, not merely trusted.

**Nothing in these three reads contradicted the task file.**

---

## Part 1 — one key, both halves

**`config/rvol.yaml`**, one setting, `rvol_anchor: rth` (values `rth`/`eth`, default `rth`), with a required `note:` enforced by its own loader (`live/attach/rvol_config.py::load_rvol_basis`) — the same strict discipline `config/ibkr.yaml` already holds every setting to. `core/indicators/context.py` stays exactly as pure as it was (**"nothing here fetches, caches, writes"** — its own docstring) — the file read lives in `live`, the one layer already allowed to touch a filesystem, and hands back the SAME `SessionBasis` shape every fixed-constant basis already is.

**One object, not two settings that agree**: `Stage2Inputs.rvol_basis: SessionBasis`, loaded ONCE per attach (`app.py`'s `_begin_attach`) and threaded through, unchanged, to both:
- **The numerator** — `attach.py`'s new `_rvol_bars(bars, basis)` narrows the price stream's always-ETH bars to `>= 09:30` in memory, at zero wire cost, ONLY for RVOL's own arithmetic — `cum vol`/`VWAP`, read from the same stream one line above, are untouched and stay ETH-wide (checked directly: `test_green_rth_anchor_excludes_premarket_from_the_numerator` asserts `cum vol` still counts the pre-market bars RVOL's own reading excludes).
- **The curve request** — `ibkr.py`'s `intraday_sessions`/`sector_sessions` now take `basis: SessionBasis` explicitly (the same pattern `daily_bars` already used), replacing the hardcoded `INTRADAY_BASIS.use_rth`. `app.py`'s `_dispatch_stage2` captures `self._stage2_inputs.rvol_basis` ONCE, on the main thread, and passes that SAME instance into the worker that issues the request — never re-read from a second place.

**The Divergence guard** (`test_083_rvol_anchor.py`) asserts this by **object identity** (`is`), not equal values — a `RecordingMD` fake captures the `basis` object each request actually received and confirms it `is inp.rvol_basis`; a second test mutates `rvol_basis` on one `Stage2Inputs` and confirms the numerator's own reading changes with it, with nothing left holding a stale copy.

`daily_bars`/`today_minutes`/ADR%/ATR/the opening range/VWAP's anchor: **untouched**, per §5.

---

## Part 2 — the row renders its anchor

`RVOL rth    0.86x own · 1.4x vs XLC` (mockup v1.6 §1). The label field widened from 9 to 12 columns for **all four value rows** — the mockup's own caption: *"so `RVOL rth` and `RVOL eth` both align with EVERY OTHER ROW"* — not just RVOL against itself, which would have needed no widening at all (both anchor words are 3 characters).

**Derived, never a literal**: `anchor_word(basis) -> "rth"|"eth"`, the one function every renderer of the anchor calls, taking `SessionBasis.use_rth` and nothing else. `Attached.rvol_anchor` is set once, at stage-1 landing (`_finish_stage1`), from the SAME `Stage2Inputs.rvol_basis` instance stage 2's own dispatch reads — so the rendered word can never name a different anchor than the one the request actually used, and it renders even while `RVOL` itself is still `pending`, because the anchor is a fact about the row known at attach, not about a value that has landed yet (`test_refusal_anchor_renders_while_pending`).

---

## Part 3 — measured, live, both anchors

**client_id=83**, real TWS, one run each per §4's own instruction ("this is a size check, not a study"):

```
rth: wall=5.73s  sessions=20  total_bars=7800   (390/session, exact — 20 x 390)
eth: wall=16.16s sessions=20  total_bars=19200  (960/session, exact — 20 x 960)
```

**Bars received exactly matched bars expected under both anchors** (B-033: no short count this run, unlike 082's own observation elsewhere — recorded as a fact about this run, not a general claim). **The bar-count reduction is 59.4% ((19200-7800)/19200)**, matching the mockup's own "~59% smaller" claim precisely. **Wall time**: 5.73s against 16.16s in this one comparison — a real, if single-run, confirmation that the RTH anchor's request is the meaningfully smaller one task 082 predicted it would be; not treated as a controlled A/B (082's own file is where that discipline lives), just the size check this task asked for.

---

## Tests — five exit categories, every one seen red first

`live/tests/test_083_rvol_anchor.py`, 10 tests: Green ×2 (the anchor changes the request and the render together — RTH excludes pre-market from RVOL's own numerator while `cum vol` stays ETH-wide; ETH includes it and the row names `eth`), Divergence ×2 (object identity across the curve request and the numerator filter; mutating the one object moves both halves together), Derived label ×2, Refusal ×2 (the anchor renders while `pending` and while `unavailable` alike), Fixture ×1 (checked by AST import-inspection that nothing here is borrowed from `test_attach.py`'s shared `Fake`), plus a Part-0 pin (the config's own default is `rth`).

**Confirmed RED via `git stash`** of `live/attach/attach.py`/`ibkr.py`/`live/tui/app.py`/`day_record.py` (and hiding the new `rvol_config.py`/`config/rvol.yaml`) against the real pre-083 tree: `ModuleNotFoundError: No module named 'live.attach.rvol_config'` at collection. `git stash pop` restored the fix; full suite re-confirmed green after.

**Four existing tests needed updates, none of them 078's** (078's own tests untouched — see 080's done-note for that precedent, unaffected again here):
- `Fake`/`QQQFixture` (`test_attach.py`, `test_qqq_2026_08_13_regression.py`) — `intraday_sessions`/`sector_sessions` gained a `basis=None` parameter, matching the Protocol's new signature.
- `stage2_of` (`test_attach.py`'s shared helper) — now passes `inp.rvol_basis` into both calls, matching what `app.py`'s real dispatch does.
- `test_a_key_press_renders_the_context_block_not_only_the_symbol` (`test_attach_is_reachable_by_key.py`) — its own `useRTH` assertion required ALL `"1 min"` requests to be `False`; now correctly asserts the price stream (`"1 D"`) stays `False` while the RVOL curve (`"20 D"`) is `True` by default — the two `1 min` requests carry genuinely different bases now, which is the whole point of this task, not a regression the old assertion should be trusted to catch.
- My own `test_080_two_stage_attach.py::test_green_rvol_renders_both_labelled_readings_in_ruled_order` — updated its exact-wording assertion for the wider 12-column field and the new anchor word, since it now tests the CURRENT mockup (v1.6) rather than v1.5's shape.
- **`tests/test_session_basis.py::test_the_intraday_requests_carry_their_declared_basis`** (root-level, 038's own file — found ONLY by running the full repo suite via `verify.ps1`, not `live/` alone, which is why this is called out separately rather than folded into the list above). Its own premise was the thing 083 corrects: it asserted `intraday_sessions` fixes `INTRADAY_BASIS` unconditionally "because no caller has a choice to make" — 083's entire point is that RVOL's caller now does. Split into `test_today_minutes_carries_its_fixed_basis` (VWAP's anchor, unchanged, still asserted against the fixed constant) and a new parametrised `test_intraday_sessions_carries_whatever_basis_it_is_called_with` (RTH and ETH both asserted on the wire, not merely accepted without checking either actually reaches `useRTH`).

`live/` suite: **192 passed** (was 182 after 082). Full repo suite unaffected beyond this file's own additions (checked via `tests/test_adoption_log_complete.py`: 6 passed, all three new files logged).

---

## What you may NOT do — confirmed untouched

`request_timeout_s` — untouched. ADR%/ATR/the opening range/VWAP's own anchor — untouched, still fixed constants in `core/indicators/context.py`. No caching added (084's own, and it depends on this task). The forming-bar sawtooth — recorded in Part 0 item 2, not fixed.

---

## UAT

`christoph/open/044-for-christoph-task-uat-083-rvol-anchor.md` — live, not performed here, per the task's own instruction.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files — the tree continues to hold unrelated synced content (`christoph/open/039-046`, several `handoff/inbox/*` entries including 084/085) from other sessions/Drive sync mid-task, deliberately left untouched.

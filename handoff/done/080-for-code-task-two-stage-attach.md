---
id: 080
title: Attach becomes two stages and the panel becomes live
type: task
class: product
story: S038
epic: 4
owner: claude-code
unblocks: NOTHING
depends: none
touches: the attach path, the ATTACHED panel render, the record
uat: c043
bugs:
  - id: B-134
    action: close
    status: "Fixed. The header now renders a freshness age always (`header_freshness()` in `live/tui/app.py`) — the OLDER of the two tracked stream ages (symbol, sector). A bare header (no age token at all) is reachable and distinguishable: it fires only when `a.metrics.streams` has no entry with a non-`None` `last_update_at` — i.e. the freshness computation genuinely has nothing to report, not merely 'nothing to say.' Pinned by `test_refusal_four_states_are_all_distinguishable` in the new exit-test file."
  - id: B-114
    action: close
    status: "Closed by live measurement against real TWS (client_id=80, Sunday 2026-08-23 14:53 ET, market closed). Stage 1 keypress-to-paint: QQQ 0.250s, AMZN 0.296s wall-clock (0.25s by the internal metric both times) — matches 075's measured `reqContractDetails` floor (0.23-0.25s) almost exactly, confirming stage 1 carries no other cost. Full numbers in the measurement section below."
---

**Status** RUNNING

# 080 — attach in two stages, and four rows that keep moving

**This note needs to be pasted to chat.**

---

## Part 0 — the three reads, reported as read

**1. Does the current build refresh any panel value after attach?** Read `SPEC.md`'s `keepUpToDate` section (§ around line 1613) and then `live/attach/ibkr.py`/`live/tui/app.py` directly, not inferred. **Confirmed: nothing did.** `keepUpToDate` was never passed to any request anywhere in the tree — `_request_kwargs()` had no such key, `warm()`/`_bars()` were one-shot `reqHistoricalDataAsync` calls, and `app.py` had no timer or polling mechanism of any kind. This matches the task's own hint ("nobody has looked at the code") exactly, now verified by reading rather than assumed.

**2. What 078 left behind.** Read `live/tests/test_078_surface_the_silent_degrade.py` in full. Five tests: two (`test_the_fallback_path_consults_the_pacing_guard`, `test_the_fallback_path_refuses_once_the_guard_would_be_exceeded`) call `IBKRMarketData._bars()` directly and would go red if `_bars()` stopped calling `self._pacing.check(...)` (B-133). Three (`test_a_failed_warm_that_still_measures_reports_a_degraded_gather`, `test_a_clean_warm_reports_no_partial_at_all`, `test_warm_and_fallback_both_failing_refuses_with_a_specific_reason`) called `attach()` directly and read `r.context`/`r.rail`/`r.partial` — all three would go red the moment `AttachResult` lost those fields, **and did**. See "What changed shape" below for the disposition of each.

**3. Parallel vs. sequential stage dispatch.** Judged AFTER reading the actual threading/dispatch mechanics (`_BrokerLoop`, `_ThreadedIB`, `run_worker(thread=True)`, `call_from_thread`) rather than guessing: **built parallel.** Reasoning: stage 2's "independent landing" requirement (rows must land at their own measured times, not gated behind the slowest) is *not achievable at all* through the old `warm()` design — `reqHistoricalDataMany`'s single `asyncio.gather` returns every role together, so the fastest role's answer was never actually available before the slowest one. Achieving independent landing required each stage-2 role to be its own `run_worker(thread=True)` dispatch, each blocking on the *same* already-existing `_BrokerLoop.call()` (which is safely re-entrant from multiple threads via `asyncio.run_coroutine_threadsafe` — a documented, standard pattern, not new machinery). Once that exists, dispatching it immediately after stage 1 resolves costs nothing extra: both are non-blocking `run_worker` calls made back-to-back on the same worker thread. Building the *sequential* alternative (stage 2 waiting for stage 1's own full return, including tape/playbook) would need an *extra* deliberate synchronization point the natural design does not have — sequential is the more expensive shape to build, not the cheaper one. **Where these three reads did NOT match the task file:** none contradicted it; all three confirmed exactly what §2 of the task predicted.

---

## The mockup version discrepancy — reported, not resolved unilaterally

**Task 080's own frontmatter and §1 name `ATTACHED mockup — the context block and its states v1.4` as authoritative. The actual current Drive file (fileId `1NUPiyIrpTOldgIvIPCvj-cSmpeRrdcGn`, status CURRENT) is v1.5.** v1.5 supersedes v1.4 with exactly one additional ruling task 080's own body text never mentions: **the VWAP row loses its signed-distance suffix** (`VWAP $714.25`, not `VWAP $714.25 · +$1.28`) — v1.5's own §2: *"`Last $` and `VWAP` read the same number while the distance claimed $1.28 between them... the moment `Last $` joined the panel the two became checkable, and the drawing was not re-read. Third firing of B-127."*

**Built against v1.5**, per this project's own governance ("the last screen mockup outranks any spec it contradicts on what renders") and per Part 0's own instruction to report rather than silently pick. `_vwap_row()` in `live/tui/app.py` renders the value alone; `VWAP_ext` is no longer computed anywhere.

**A second, larger discrepancy, found the same way and worth Christoph's attention directly: `christoph/open/039-for-christoph-decision-two-stage-attach.md` and `christoph/open/042-for-christoph-decision-live-rows.md` are both still OPEN (unresolved, never retired to `christoph/done/`).** c039's own Ruling 2 *recommends* stage 1 fetch "contract details only... nothing streaming" — the opposite of what task 080's body text and the v1.5 mockup both ask for. c042 frames the live-price/continuously-updating mechanism as **story S039, explicitly separate from S038's two-stage split** ("could ship before it"), while task 080 is filed under `story: S038`. Built to task 080's own text and the v1.5 mockup regardless — those are what this session was actually handed as the work order, and `christoph/open/043` (this task's own UAT) already exists, which only makes sense if S038 was understood to include the live-row mechanism by the time that UAT was written. **But the paperwork is inconsistent**: either c039/c042 were answered informally and never retired, or S038/S039 were deliberately merged and the decision files were never updated to say so. Recommend Christoph either retire c039/c042 with a note pointing at 080, or split the two stories properly if the merge was not intended.

---

## Part 1 — the two stages, as built

**Stage 1** (`attach()` in `live/attach/attach.py`, now shrunk to steps 1/2/tape/playbook — no historical request of any kind) resolves the contract, checks cooldown and the tick slot, opens the tape, binds the playbook, and returns. Measured floor unchanged: ~0.25s.

**The live price stream** (`IBKRMarketData.open_price_stream` in `live/attach/ibkr.py`) is new: one `keepUpToDate=True` request per stream (symbol always; sector only if a mapping exists), the SAME `"1 D"`/`"1 min"`/`INTRADAY_BASIS.use_rth` shape the retired `today`/`sector_today` roles used as one-shot pulls — **this replaces those roles rather than duplicating them**. `_ThreadedIB.reqHistoricalDataStream` fires `on_update` once with the initial payload (so `Last $`/`VWAP` don't wait an extra ~5s cadence beat for data that already arrived) and again on every subsequent `updateEvent`.

**Stage 2's three remaining one-shot roles** (`rth_dailies`, `sessions`, `sector_sessions` — unchanged shape/duration/size from before) are each dispatched from `app.py`'s `_dispatch_stage2` as an independent `run_worker(thread=True)`, calling the market data client's existing `daily_bars`/`intraday_sessions`/`sector_sessions` methods directly (no `warm()` in the middle — see "What changed shape" below).

**Which rows read which inputs**, and why the request count did not grow even though a wire request was added:
- `Last $`, `VWAP`, `cum vol` — the symbol price stream alone.
- `ADR% used` (and the level rail, and the unrendered SMA stack) — `rth_dailies` alone, **self-sufficient**, exactly as before (its `price` term is `rth_dailies[-1].close`, never the stream's).
- `RVOL`'s own reading — `sessions` (the curve) + the symbol stream (today's cumulative volume).
- `RVOL`'s sector-relative reading — `sector_sessions` + the sector stream.

Net: the OLD `warm()` batch fetched 5 one-shot roles (`rth_dailies`, `today`, `sessions_raw`, `sector_today`, `sector_sessions_raw`) when a sector mapping existed. The NEW dispatch fetches 3 one-shot roles + opens 2 streams = the same 5 requests, just 2 of them are now opens rather than one-shots — confirmed live (AMZN's run below shows exactly 2 streams + `rth_dailies` + `sector_sessions`; `sessions` timed out but was still dispatched, making 5).

**`compute_context_and_rail(inp: Stage2Inputs)`** (`live/attach/attach.py`) is the mechanism independent landing runs on — a pure function called by `app.py` every time one more input lands (a stream tick or a role's completion), returning whichever rows are currently computable. A key absent from its return is pending; nothing is ever un-computed once landed. This is what replaces the retired `_context_block`.

**Cancel-on-switch**: `_begin_attach` cancels every `StreamHandle` the outgoing symbol opened and bumps `self._attach_generation`. Every stage-2 callback (`_apply_stream_update`, `_apply_role_landed`, etc.) checks its own captured generation against the current one before touching `self.record`, so a callback already in flight from a superseded attach is inert even if the underlying wire request could not itself be aborted.

---

## Part 2 — the rows, as built

Five rows: symbol, `Last $`, `ADR% used`, `RVOL`, `VWAP`. `CONTEXT_ORDER` in `app.py`.

- **`Last $`** — never literally `pending` (the task's own instruction). Its brief pre-first-tick state uses the grammar's existing `not_yet`/`warming` wording instead, since structurally it is a different kind of wait (a stream opening, never bounded at 60s) from the other three rows' historical fetch.
- **`RVOL`** — `0.86× own · 1.4× vs XLK` (or whatever the real sector ETF symbol is — `Attached.sector_etf`, a new field, carries the string so the label is never hardcoded). Own-history reading first (the one `compute_context_and_rail` computes first, matching the mockup's own "the one read first" reasoning), sector-relative second. `avg`/`rel`/`cum` are retired as labels. `cum vol` stays computed (read off the price stream, same arithmetic as before), never rendered on this row — checked by text-absence, not field-absence, the opposite of B-028's `ADR$` treatment, per the task's own instruction.
- **`VWAP`** — value only, per the v1.5 discrepancy above.
- **Pending, per row, independently** — `context_rows()` derives it from key-absence in `a.context`; no shared paint, no summary count, no `a.partial` line (retired — see below).

**Refusal independence extended to the new pending state**: B-117 ("one reading refusing never blanks the other") already held for RVOL's two readings; this task extends the same property to *pending*, since a genuinely reachable state is "own landed, sector reading still in flight" (own's `sessions` pull is typically much faster than the sector's). Tested directly in `test_a_refused_sector_reading_does_not_blank_the_own_reading` and `test_a_pending_sector_reading_does_not_blank_the_own_reading`.

---

## Part 3 — freshness

**"Amber" renders as text, not colour — a deliberate, load-bearing finding, not an oversight.** Read the whole render layer (`grammar.py`, `links.py`, `app.py`'s own module docstring) before writing anything here: this codebase has **no** literal terminal-colour rendering mechanism anywhere. Every existing state distinction (`~`, `?`, `[ ]`, `—`, the violet-marker convention `links.py` documents for a *future* colour) is already purely typographic, explicitly so it "survives 16-colour degradation over SSH." `grammar.py` already carries an unused `Cell.stale(text, age)`/`Freshness.STALE` primitive that was evidently built for exactly this and never wired up. **"Amber" is realised as the literal word `stale` in the text** (`stale 34s`), matching the mockup's own ASCII rendering exactly, and reusing the codebase's one consistent state-distinguishing convention rather than inventing a first colour-rendering layer this task did not ask for. Stated explicitly since it is an interpretive call, not something either the task file or the mockup states in so many words.

**Exactly two tracked stream ages** — task 080's own text: *"Two streams, two independent ages"* — `symbol` (backs `Last $`/`VWAP`/`ADR% used`/`RVOL`'s own reading) and `sector` (backs `RVOL`'s sector-relative reading alone). Per the mockup's own stale-example screen (confirmed against my full read of v1.5 §4): even with the header stale, `Last $`/`ADR% used`/`VWAP` render with NO stale suffix of their own — only the header and RVOL's two sub-readings ever carry one. Built exactly that way; no other row's cell code has a stale branch.

**Header**: always renders an age (`header_freshness()`), the older of the two tracked ages; bare only when neither stream has ever delivered an update (B-134, closed above). 20s threshold, `STALE_THRESHOLD_S` in `app.py`, explicitly marked unfitted in its own docstring per the task's instruction (008b: median 5.002s, max 14.477s, one 32-minute session).

---

## Part 4 — measurements

`Attached.metrics: AttachMetrics` (`day_record.py`) — `streams: dict[str, StreamMetrics]` (symbol/sector, never pooled — update count, last-update timestamp, a capped inter-update gap list, an error string), `requests: dict[str, RequestMetrics]` (per role — wall time, bars received, `bars_requested` always `None`: duration/bar-size are not a literal count and I did not invent a trading-calendar model to estimate one, per the task's own "nothing you write may imply a certainty the measurement does not have"), and per-stage keypress-to-paint. Rendered only by `attach_metrics_rows()`, spliced into HEALTH; `context_rows()` (ATTACHED) never reads `.metrics` at all — pinned by `test_measurements_never_render_on_attached`.

---

## What changed shape from 078, and why (§7's explicit requirement)

**078's pacing-guard guarantee (B-133) survives completely unchanged and untouched** — `_bars()` still calls `self._pacing.check(...)` before every request, and since NOTHING calls `warm()` from the live dispatch path any more, `daily_bars`/`intraday_sessions`/`sector_sessions` now *always* fall through to `_bars()` (never a cache hit), which means B-133's guard is exercised on literally every stage-2 request rather than only on the fallback path — a stronger guarantee than before, achieved with zero code changes to `ibkr.py`'s pacing logic. `warm()`/`_ROLES`/`_warm`/`_warmed()`/`call_many()`/`reqHistoricalDataMany()` are left in place, unused by the new dispatch, deliberately not deleted — smaller, more conservative diff, and nothing in this task asks for their removal.

**078's surfaced-degrade guarantee (B-130) does not survive in its old SHAPE, because the failure mode it existed to catch is structurally gone.** B-130 was specifically about a *hidden distinction* between "the batched `warm()` call failed" and "a row's own fallback failed" — two different failure sources that could combine and silently mask each other. There is no more batched `warm()` call in the live dispatch path: every stage-2 role's ONE call IS its only read, so a role's failure IS that row's own refusal, directly, with its own specific reason — there is nothing left to silently mask it *behind*. `AttachResult.partial`/`Attached.partial` (the screen-level "N of M rows unavailable" summary that carried B-130's combined message) are removed — 080's own five-rows-and-header constraint (§4/§7) leaves no line for it, independent of B-130's status.

**`live/tests/test_078_surface_the_silent_degrade.py` rewritten**: the two Guard tests (`test_the_fallback_path_consults_the_pacing_guard`, `test_the_fallback_path_refuses_once_the_guard_would_be_exceeded`) are **byte-identical, untouched**. The three Green/Refusal/control tests that read `attach()`'s now-removed `context`/`rail`/`partial` are replaced by two new tests that check the guarantee 078 actually needed in its new, simpler shape: `test_every_stage2_role_call_consults_the_pacing_guard` (asserts `daily_bars`/`intraday_sessions` — the exact calls `app.py` now makes — both touch `_PacingGuard`) and `test_a_role_failure_renders_its_own_reason_not_a_generic_default` (asserts `daily_bars` propagates a specific exception message rather than a generic default, at the client layer directly — the arithmetic-layer version of the same guarantee is `test_attach.py::test_refusal_a_a_failed_request_leaves_the_others_rendering`).

**`test_attaching_state.py`'s two `.partial`-dependent tests** (`test_a_partial_attach_carries_a_screen_level_statement`, `test_an_explicit_failure_widens_the_unavailable_count`) rewritten to `test_a_partial_attach_names_the_specific_row_and_reason` and `test_an_explicit_failure_refuses_a_row_the_baseline_does_not` — same underlying property (a failure is visible, and an explicit failure produces more refused rows than the clean baseline), asserted against the per-row render instead of the retired summary field.

**`test_071_four_row_context_block.py` and `test_qqq_2026_08_13_regression.py` and `test_rendered_rows_declare_basis_and_unit.py` and `test_attach.py` and `test_attach_is_reachable_by_key.py`** all needed updates purely because `AttachResult` lost `context`/`rail`/`partial` — none of these are 078's files, all are prior tasks' (070/071/038/032/034) fixture files whose row shape this task's own §9 explicitly reverses (S037 criterion 3, B-095, B-096). Full list of touched test files: 12 (see `git diff --stat` in the commit).

---

## A real, live race found and fixed along the way, unrelated to any bug ticket

Driving the pilot tests with the new multi-worker stage-2 dispatch surfaced a genuine flake: `_rerender()` used to do `frame.remove_children()` **outside** `_apply_fit`'s lock, then call `_apply_fit()` separately — safe when only one caller ever rendered at a time (058's single atomic swap), unsafe once many independent callback sites (`_apply_stream_update`, `_apply_role_landed`, ×5 workers per attach) can each call `_rerender()` concurrently. Reproduced standalone (`no ATTACHED panel on screen` / `NoMatches('#frame')`, ~1 run in 5-8) and fixed by folding the remove-then-mount decision into ONE atomic step under `_fit_lock` (`_apply_fit(force=True)`), extending exactly the guarantee `060`/B-001 already established for concurrent resize-vs-attach to concurrent attach-vs-attach. Separately, every pilot test's `wait_for_complete()` call needed to become two calls (`_settle()` helper in `test_attaching_state.py`, matching pattern in `test_072_attach_switches_symbol.py` and `test_attach_is_reachable_by_key.py`'s `type_symbol`) — stage 1's worker dispatches stage 2's several workers from *inside* its `call_from_thread` callback, so a single `wait_for_complete()` can return before they are registered. This second issue is test-harness-only (no production race — the real app never "waits for complete," it just keeps running); the first is a genuine production fix.

---

## Tests — full suite, and every new/changed test seen red first

`live/tests/test_080_two_stage_attach.py` — new, 10 tests (Green ×3, Refusal ×2, Colour ×2, Part 4/HEALTH ×2, Fixture ×1). **Every state in this file is constructed locally**, checked by AST import-inspection (`test_fixture_every_state_here_is_constructed_not_borrowed_from_a_shared_fake`) rather than trusted by review — none of it reads a gap `test_attach.py`'s shared `Fake` happens to leave, the exact trap 078 found.

**Red confirmed via `git stash`**: stashed `live/attach/attach.py`, `live/attach/ibkr.py`, `live/tui/app.py`, `live/tui/day_record.py` (and moved the new `streaming.py` aside) back to the real pre-080 (078) state; `test_080_two_stage_attach.py` failed collection with `ImportError: cannot import name 'Stage2Inputs' from 'live.attach.attach'` — confirmed red against the real tree, not a synthetic double. `git stash pop` restored the fix; full suite re-confirmed green twice after (172 → 182 passed, stable across repeated runs).

**Full `live/` suite: 182 passed, 0 failed**, run twice for stability given the race found above. (078 left it at 173; net across every file this task touched: −1 from consolidating 078's 5 tests to 4, +10 from the new file, and the rest are in-place rewrites of existing tests, not new ones.)

`tests/test_adoption_log_complete.py`: 6 passed — `live/attach/streaming.py` and `live/tests/test_080_two_stage_attach.py` both logged in `ADOPTION-LOG.md`.

---

## Live measurement against real TWS — closes B-114

**client_id=80** (matching this task's number, never `7`/`75`/`121`/`11`), read-only, port 7496 confirmed open immediately before connecting. **Run 2026-08-23 14:53 ET, after-hours trading — low volume, not a regular session.** Stated plainly because it bounds what this measurement can and cannot claim: stage 1's speed and stage 2's independent-landing/refusal behaviour are genuinely observed live; the price stream's *ongoing* ~5s cadence (008b's own claim, measured during a regular RTH session) was **not** independently re-confirmed here — both streams delivered their initial payload correctly, but only one update apiece was observed in this run, consistent with genuinely low after-hours volume rather than a defect. Worth a repeat measurement during regular hours before the ongoing-cadence claim is trusted for this build specifically (008b measured the mechanism, not this integration of it).

```
QQQ:  keypress-to-paint = 0.250s wall-clock (0.25s internal metric)
      stage2 first row: 21.11s (rth_dailies, 251 bars)
      stage2 last row:  33.09s (sessions, 19200 bars — 20 sessions × 960 min)
      all rows landed ok: ADR% used, Last $, RVOL, RVOL_rel, VWAP

AMZN: keypress-to-paint = 0.296s wall-clock (0.25s internal metric)
      stage2 first row: 3.94s  (rth_dailies, 251 bars)
      role sector_sessions: 47.72s (14925 bars)
      role sessions: TIMED OUT at 60s (request_timeout_s) — 0 bars, error
        "no answer in 60s (request_timeout_s)"
      RVOL's OWN reading refused (— (no answer in 60s ...)); RVOL_rel,
      ADR% used, Last $, VWAP all landed ok regardless — B-117 held live,
      not merely in a fixture.
```

**Stage 1 closes B-114**: 0.25-0.30s, matching 075's measured `reqContractDetails` floor, confirming stage 1 carries no cost beyond contract resolution — exactly the point of the split.

**A real, unplanned refusal observed live** (AMZN's own 20-session pull hitting `request_timeout_s`) confirms Part 2's independence guarantee against a genuine failure, not only a fixture's simulated one — and confirms `request_timeout_s` itself was not touched (per §7's explicit prohibition; it fired exactly as configured).

Harness: `$CLAUDE_JOB_DIR/tmp/080_stage1_measure.py`, scratch, not committed, per §7.

---

## What this reverses (§9, restated as built)

**B-095** (no per-cell pending state) — reversed; every row has one. **B-096** (progressive fill ruled out) — reversed; rows land independently, confirmed live (21.1s vs. 33.1s for QQQ; 3.9s vs. 47.7s/timeout for AMZN). **S037 criterion 3** (one paint) — reversed. **Not reversed**: B-116 (old values drop together on re-attach) — untouched; `_begin_attach`'s unconditional cancel + generation bump is exactly the mechanism that keeps this true while ALSO allowing the new symbol's rows to land independently of each other.

---

## What you may NOT do — confirmed untouched

`request_timeout_s` — untouched (config, and confirmed firing correctly live above). No historical request's duration/bar-size/`use_rth` changed — `rth_dailies`/`sessions`/`sector_sessions` are byte-identical shapes to before; only the `today`/`sector_today` roles were *replaced* by streams of the identical shape, not resized. ATTACHED renders exactly five rows and the header, nothing more. No measurement harness committed.

---

## UAT

`christoph/open/043-for-christoph-task-uat-080-two-stage-attach.md` — live, during a regular session (this session's own live measurement ran after-hours and cannot substitute for it, particularly for the ongoing stream-cadence claim above). Not performed here, per the task's own instruction.

---

## Closing sequence

`verify.ps1` runs as the last action, per §10 — not pasted or summarised here. `export-handoff.ps1`/commit/push follow, from the main checkout, scoped to this task's own files — the tree currently also holds unrelated synced content (`christoph/open/039-043`, `handoff/inbox/066,067,073,076,077`) from another session/Drive sync mid-task, deliberately left untouched and unswept.

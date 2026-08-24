---
id: 084
title: The reduced RVOL curve is cached in memory for the trading day
type: task
class: product
story: S034
epic: 4
owner: claude-code
depends: 083
touches: the RVOL curve fetch and reduction path
mockup: ATTACHED mockup — the context block and its states
uat: c045
bugs:
  - id: B-138
    action: confirm
    status: "The task's own frontmatter names this action `mitigate`; the done-note vocabulary (`tests/test_donenote_bugs_block.py::ACTIONS`) does not include that verb, so this row uses `confirm` — B-138 already exists (082 confirmed it by measurement, not by fixing it) and this task updates its status rather than closing it. The cache removes the repeated request/reduction cost on every attach after the first; it does not change what RVOL computes, does not fix the forming-bar sawtooth (082/083's own open item), and does not address the underlying pacing contention 082 measured (15-60s, 60% timeout rate on AMZN) for a COLD symbol — a session that only ever attaches names it has not seen before gets none of this benefit. The live number this task exists to produce (second-attach wall time against the first) is NOT YET MEASURED — see Part 3 below — so this row cannot be closed on this note."
---

**Status** RUNNING

# 084 — cache the curve, not the bars

**This note needs to be pasted to chat.**

---

## Part 0 — read first, reported as read

**1. `warm()`/`_ROLES`/`_warmed`/`call_many` in `live/attach/ibkr.py` — read directly, not reused.** All four are real and still in the tree, but none is the primitive this task needs:

- **`_ROLES`/`warm()`/`_warmed()`** is a WITHIN-ATTACH cache of RAW bars, keyed on a single field, `self._warm_symbol` — a second `warm()` call for a different symbol **overwrites** `self._warm`/`self._warm_symbol` outright, so it cannot hold more than one symbol's data, has no anchor axis and no session-date axis, and caches the ~19,200 raw bars this task's own §3 explicitly forbids caching. **It is also dead from the live dispatch path since task 080** — `app.py`'s `_role_worker` calls `daily_bars`/`intraday_sessions`/`sector_sessions` directly, never `warm()`, so `_warm_symbol` stays unset for the whole life of the real program and `_warmed()` always returns `None`. A second cache built alongside a dormant first one would be a second store, and this one is not merely dormant — it is the wrong shape on every axis this task's key needs (symbol **and** anchor **and** session date, surviving across attaches, holding the reduced curve only).
- **`call_many()`** is a concurrent-dispatch primitive (N requests via one `asyncio.gather`, on `_ThreadedIB`) — it batches wire calls, it does not avoid them. Unrelated to storage.

**Built new: `RvolCurveCache` in `live/tui/app.py`.** See Part 1.

**2. How the session date is currently determined — nowhere, before this task.** Grepped the tree: `DayRecord.session_date` is a field nothing sets or reads, anywhere. Populating that dead field is a separate, larger decision this task does not need to make (it would mean deciding what else should key off "the record's own day," which nothing today asks for). Defined fresh, narrowly, for the cache's own purpose only: `_session_date() -> str`, `datetime.now(EASTERN).strftime("%Y-%m-%d")` — midnight ET is the right boundary for "is this still the same trading day for caching purposes," and it does not need `risk.yaml`'s 09:30 P&L-rollover boundary, which answers a different question.

---

## Part 1 — what is cached, and the bound

**The reduced curve only** — `rvol_curve()`'s own output, ~390 per-minute medians, never the ~19,200 raw bars they came from. Reduction happens on the WORKER thread inside `_role_worker` (CPU-bound, not I/O — costs nothing extra to do off the main thread), so `_apply_role_landed` and the cache itself never see a raw bar.

**Key: `(symbol_or_etf, anchor_word, session_date)` — all three**, exactly as the task specifies. The sector half is keyed on the ETF symbol (`contract.sector_etf`), never on the attached symbol, so two symbols mapping to the same sector share one cache entry — checked directly by `test_key_isolation_two_symbols_sharing_a_sector_etf_hit_on_the_sector_curve`.

**In memory only.** `RvolCurveCache` is a plain `collections.OrderedDict` on `MomentumApp`, constructed once in `__init__` and never reset by `_begin_attach` — the one place in the attach lifecycle that already resets everything else per-attach (`Stage2Inputs`, streams). Nothing here touches disk.

**Bound: 20 entries, LRU on last-served, not last-inserted.** `RVOL_CURVE_CACHE_MAX = 20` — a session cycles through a handful of tickers repeatedly, not dozens; 20 covers a generous watchlist with headroom without letting the cache grow across an unbounded session. `RvolCurveCache.get()` calls `OrderedDict.move_to_end()` on every hit, so the entry evicted when the bound is exceeded is the one nobody has re-read, not merely the one inserted longest ago — `test_bounded_the_cache_evicts_the_least_recently_served_entry` pins this by re-serving the oldest entry and confirming a DIFFERENT one is dropped.

**Never a partial or empty curve.** `.put()` is called from exactly one place, `_apply_role_landed` — the SUCCESS path. `_apply_role_error` (the failure path) never references the cache at all, so a failed fetch structurally cannot populate it; not merely convention, checked by `test_refusal_a_failed_fetch_does_not_populate_the_cache`.

---

## Part 2 — how it behaves

**A hit skips the request entirely.** `_dispatch_stage2` checks the cache on the MAIN thread, before dispatching anything — a hit calls `_apply_cached_curve` synchronously (`wall_s=0.0`, no bar count, no `run_worker`, no `_PacingGuard` consultation, because no request is made) and repaints once at the end if any role hit. A miss dispatches `_role_worker` exactly as before 084, now carrying the cache key so a SUCCESSFUL landing can write it.

**Cancel-on-switch does not evict.** `_begin_attach` cancels the outgoing symbol's price STREAMS (`self._streams`); it does not touch `self._rvol_curve_cache`. Attaching away from AMZN and back within the same session, same anchor, same day is a hit.

**Do-not list, confirmed untouched:** no disk/file/database; nothing cached but the reduced curve (`rth_dailies`, the sector mapping, the price stream are all unaffected); RVOL's arithmetic is unchanged, only where the curve comes from; the forming-bar sawtooth (Part 0 item 2 of 083's own note) is not addressed; `request_timeout_s` is untouched.

---

## Tests — five exit categories, every one seen red first

`live/tests/test_084_rvol_curve_cache.py`, 8 tests. **Every state is self-built** — `_MD`, a `MarketData` written for this file alone, never `test_attach.py`'s shared `Fake()` or `test_attach_is_reachable_by_key.py`'s `drive()`/`type_symbol()` (B-136; checked by the same AST-import test 083 introduced).

**`_MD`'s defining property**: `intraday_sessions`/`sector_sessions` share ONE call counter, and each call answers a HIGHER-volume curve than the one before. This is what makes the Identity test mean something — a coincidence where a static fixture answers the same value twice would prove nothing; here, a second live fetch is guaranteed to produce a MEASURABLY DIFFERENT RVOL reading, so two equal readings are proof the cache served the request, not proof the fixture agreed with itself.

- **Green** (`test_green_second_attach_of_the_same_symbol_issues_no_curve_request`): drives a real `MomentumApp` through two full keypress-driven attaches of QQQ. After the first, exactly one own and one sector curve request are recorded. After the second, still exactly one of each — no new request — and the rendered `RVOL` value is unchanged.
- **Identity, the important one** (`test_identity_the_cached_curve_is_the_first_fetch_not_a_fresh_recompute`): reads the cache directly after the first attach (`app._rvol_curve_cache.get(key)`), confirms it is populated, then confirms the second attach's `RVOL` value is bit-for-bit equal to the first's — which, given `_MD`'s rising-volume answers, could only be true if the second attach served the cached curve rather than a fresh one. Also confirms `app._stage2_inputs.sessions == cached_curve` value-for-value.
- **Key isolation, three tests, each red for a different reason**: `test_key_isolation_changing_the_anchor_misses` (monkeypatches `load_rvol_basis` to answer RTH then ETH across the two attaches — 2 own requests, not 1); `test_key_isolation_changing_the_session_date_misses` (monkeypatches `_session_date` the same way); `test_key_isolation_two_symbols_sharing_a_sector_etf_hit_on_the_sector_curve` (AMZN then MSFT, both mapping to `XLC` — 1 sector request across both attaches, but 2 own requests, since the own half is never shared across symbols).
- **Refusal** (`test_refusal_a_failed_fetch_does_not_populate_the_cache`): `_MD` set to fail `sessions`; confirms `app._stage2_inputs.sessions_failed` is set, confirms the cache key is absent afterward, and confirms a THIRD attach still attempts a real fetch rather than being permanently blocked by a phantom entry.
- **Bounded** (`test_bounded_the_cache_evicts_the_least_recently_served_entry`): direct unit test of `RvolCurveCache`'s LRU behaviour, described in Part 1.
- **Fixture** (`test_fixture_this_file_builds_every_state_itself`): AST import-inspection, same shape as 083's.

**Confirmed RED via `git stash`** of `live/attach/attach.py`, `live/tui/app.py`, and this task's own test-helper fixes (`test_attach.py`'s `stage2_of`, `test_qqq_2026_08_13_regression.py`'s `_attached()`, and the raw-bars-assigning tests in `test_083_rvol_anchor.py`/`test_080_two_stage_attach.py`) against the real pre-084 tree: `ImportError: cannot import name 'RVOL_CURVE_CACHE_MAX' from 'live.tui.app'` at collection. `git stash pop` restored the fix; full `live/` suite re-confirmed green after (200 passed, was 192 after 083).

**A real breaking change surfaced mid-task and was fixed as part of this same task, not deferred**: `Stage2Inputs.sessions`/`.sector_sessions` changed TYPE (raw bars → the reduced curve, since reduction now happens once, on the worker thread, ahead of the cache write) — every test helper that builds a `Stage2Inputs` directly and feeds it raw bars had to start wrapping the assignment in `rvol_curve()` to match. Four files needed this: `test_attach.py`'s `stage2_of` helper, `test_qqq_2026_08_13_regression.py`'s `_attached()` helper, four tests in `test_083_rvol_anchor.py`, and one test in `test_080_two_stage_attach.py`. None of 078's own tests were touched (same precedent 080/083 both record).

**Full repo suite**: 611 passed, 12 failed — **all 12 are pre-existing, unrelated to this task**, and concern `christoph/`/`handoff/` frontmatter, the UAT review register, and `REGIME-PROMPT.md`'s `6 of 9` wording — synced-in content from other sessions/Drive mid-task (`christoph/open/039-046`, several `handoff/inbox/*` entries), none of it touched by this task's own files. Not fixed here, per the product/admin line: these are admin findings on files this task does not own, and this task's own scope is the RVOL cache. `tests/test_adoption_log_complete.py`: 6 passed, all three 083 files plus this task's own new test file logged.

---

## Part 3 — measurement: NOT YET DONE

**TWS is not running as of this note.** The task's own §7 is explicit that the live wall-time measurement — a second attach of the same symbol against the first — "is the whole point of the task," so this is recorded as owed rather than skipped or estimated. A scratch harness (`084_cache_measure.py`, never committed) is written and ready: it drives a real `MomentumApp` + Textual pilot against real TWS (`client_id=84`), attaches QQQ, waits out IBKR's own same-symbol historical cooldown (15s, on the `rth_dailies` role, which this task does not cache), attaches QQQ again, and reports keypress-to-`RVOL`-landed wall time for both, plus the own-role `RequestMetrics.wall_s`/`bars_received` for each and an identity check on the rendered value.

**This mirrors 058 → 075 exactly**: 058's own live measurement was blocked mid-session when TWS went unreachable, recorded as owed rather than fabricated, and completed later once TWS was reachable again. The same discipline applies here — this note's own `**Status**` stays `RUNNING`, not `DONE`, until the measurement is added.

---

## What you may NOT do — confirmed untouched

`request_timeout_s` — untouched. RVOL's arithmetic — untouched, only where the curve comes from changed. The forming-bar sawtooth — not fixed, recorded again rather than silently left. Nothing cached but the reduced curve.

---

## UAT

`christoph/open/045-for-christoph-task-uat-084-curve-cache.md` — live, not performed here, per the task's own instruction. **Cannot meaningfully be performed until Part 3's measurement exists**, since the UAT is presumably about the speedup this note cannot yet quote.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files — the tree continues to hold unrelated synced content (`christoph/open/039-046`, several `handoff/inbox/*` entries including 085) from other sessions/Drive sync mid-task, deliberately left untouched, per the same precedent 083's own note recorded.

**This note needs to be pasted to chat, and needs a follow-up once the live measurement lands** — either later in this session if TWS comes back up, or as a small follow-on task otherwise.

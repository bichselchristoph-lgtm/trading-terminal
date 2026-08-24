---
id: 088
title: ADR% used reads 106.8% at an 04:00 attach — establish what its numerator is drawn from
type: task
class: product
story: S036
epic: 4
owner: claude-code
depends: none
touches: the ADR% computation and the request behind it
mockup: ATTACHED mockup — the context block and its states
uat: c048
bugs:
  - id: B-142
    action: close
    status: "Fixed. Candidate A confirmed by reading, Candidate B does not hold — see Part 0. `Stage2Inputs` gains `today_et` (ET calendar date, captured once by `app.py`'s `_begin_attach`, defaults to `\"\"` so every pre-088 test is unaffected); `compute_context_and_rail`'s `ADR% used` branch now refuses with `session not started` when `rth_dailies[-1]`'s own date does not match it, instead of reading a closed session as if it were today in progress. Confirmed red against pre-fix code via `git stash` of the two changed files (5 of 7 new test categories failed correctly, the escape-hatch and Fixture tests correctly still passed), green restored. Fixing the check surfaced two pre-existing shared fixtures (`test_attach.py`'s `Fake`, `test_attach_is_reachable_by_key.py`'s `FakeIB`) whose hardcoded daily-bar dates now read as stale under a real attach — both stamp their LAST daily bar to the real current date; see Tests."
  - id: NEW
    action: raise
    status: "Raised, not fixed — out of this task's scope (§5: 'the numerator and its basis are' the only thing in scope). `attach.py`'s level rail derives `PDH`/`PDL` as `prior[-2]` on the assumption `prior[-1]` (`rth_dailies[-1]`) is today in progress — the exact assumption Part 0 shows is false at a pre-open attach. At an 04:00 attach, `rth_dailies[-1]` is the last COMPLETED session (say Friday), so `prior[-2]` (labelled \"prior session\") is actually the session BEFORE that (Thursday) — PDH/PDL is off by one session for the duration of the pre-open window. Same root cause as B-142, different row, not fixed here — `compute_context_and_rail`'s rail branch (attach.py:441-471) was deliberately left untouched per §5's 'do not touch... the rail' reading. Worth a B number and its own task; not raised as an emergency since the window it is wrong in is bounded (attach before the session's first RTH print) and PDH/PDL is not the row 088's own bug report was about."
---

**Status** RUNNING

# 088 — one bar wearing "today" without being checked

**This note needs to be pasted to chat.**

---

## A concurrent-session finding, checked before anything else

`087`'s own done-note records that a peer session (`momentum-32`) had left **substantial uncommitted, in-progress work for this exact task** sitting in `live/attach/attach.py`/`live/tui/app.py` — `today_et`/`session not started` logic, never committed (`git log -S "today_et"` returned nothing at the time `087` checked).

**Re-checked at the start of this session, before any edit**: `git status --short` showed both files clean, and `git log -S "today_et" -- live/attach/attach.py live/tui/app.py` (run again just now, after this task's own commits are staged but before this note's commit) still returns nothing prior to this task. `git stash list` holds one entry, unrelated (`On 054-unblock-the-queue`, predates this task by weeks). **Whatever `momentum-32` had was gone before this session started** — discarded, reset, or held in a workspace this session cannot see — and nothing of it survived into this tree. This task's diff to `attach.py`/`app.py` is confirmed, by `git diff --stat`, to be exactly this task's own work (55 and 7 lines respectively) and nothing more.

---

## Part 0 — the three reads, reported as read

**1. Which request supplies the numerator/denominator terms, and what window does it actually return at an 04:00 attach?**

`ibkr.py`'s `daily_bars(c, ADR_BASIS)` issues `useRTH=True`, `durationStr=LONG_DAILY_DURATION` (`"1 Y"`), `barSizeSetting="1 day"`, `endDateTime=""` — IBKR's own answer to "now" (`_request_kwargs`). `attach.py`'s `_adr_terms`/`compute_context_and_rail` then read `rth_dailies[-1]` unconditionally: `todays_open = rth_dailies[-1].open`, and `adr_used(inp.rth_dailies[-1].close, todays_open, dol)` — `current` is the daily bar's own close, **not** the price stream's (a pre-existing, deliberate choice, unchanged here). Nothing anywhere checked whether that last bar's own date was today's.

**2. Is that window today's session in progress, or the last completed one?**

**The last completed one, at a pre-open attach.** Before today's RTH session has printed a single trade, `useRTH=True` has nothing for today to report at all, so the LAST bar the request returns is a whole, closed session — wearing "today" only because the code assumed the newest bar always is one.

**3. Which basis does the numerator use, against a denominator labelled `ADR20 RTH`?**

**The same one, the same object, throughout.** `current`, `todays_open` (both from `rth_dailies[-1]`) and `dol` (via `_adr_terms` → `adr_pct`/`adr_dollar`, both stamped `ADR_BASIS`) are all built from the identical `rth_dailies` list, `useRTH=True` end to end. **No second flag, no second object — Candidate B does not hold.** `083`'s own assumption that ADR%'s basis is "fixed by arithmetic" is confirmed correct by this read, not merely inherited: there was nothing here for a Divergence guard to check, because nothing here ever diverges. `core/indicators/context.py` is untouched by this task.

**Candidate A is what produced 106.8%.** A whole completed session's own move (`|close - open|`) divided by a 20-session ADR$ average lands near 100% by construction — an ordinary session's own range is close to its own trailing mean — and 106.8% is one ordinary day above that average, not an accumulation of several.

---

## Part 1 — the fix

`Stage2Inputs` gains `today_et: str = ""` (`live/attach/attach.py`) — the ET calendar date, threaded in from the one layer allowed to touch a clock (`app.py`'s `_begin_attach`, the same moment `since` is captured, same `EASTERN` zoneinfo). `""` is the default every pre-088 test leaves it at, and the day-boundary check below does not run when it is unset — the same absent-means-pending idiom `rvol_basis`'s own default note already uses, chosen deliberately so this field's arrival changes no test this task did not itself write.

`compute_context_and_rail`'s `ADR% used` branch now reads:

```
last_bar_date = inp.rth_dailies[-1].ts[:10]
if inp.today_et and last_bar_date != inp.today_et:
    out["ADR% used"] = Measured.absent("session not started")
else:
    ... unchanged ...
```

**The RVOL-precedent refusal wording** (§4's own instruction) — `RVOL rth`'s `"no bars today"` is the shape this follows: a row that knows its own window has not started says so, distinguishable both from a computed value and from `inp.rth_dailies_failed`'s own fetch-refusal text (three states, not two — see Tests).

**`ADR20`'s own definition is untouched** — `adr_pct`, `adr_dollar`, `ADR_BASIS` in `core/indicators/context.py` are byte-identical to before this task. **No config key added** — Candidate B did not hold, so §5's conditional prohibition never triggers.

**Not fixed, and said here rather than left implicit:** `ext 10/20/50` (the unrendered SMA-extension rows, `attach.py:353-354`) still read `inp.rth_dailies[-1].close` unconditionally inside the same `else` branch — they inherit the fix's gate (they no longer compute at all during the refusal window, since they sit inside the same `else:`) but were not separately audited, because nothing renders them (`CONTEXT_ORDER` excludes them, unchanged since `080`).

---

## Tests — five exit categories from §6, one file

`live/tests/test_088_adr_day_boundary.py`, 7 tests:

- **Green ×2** — `rth_dailies[-1]` dated today computes normally, on the one `ADR_BASIS` object throughout (Part 0 item 3, asserted directly by `is`, not equality); `today_et == ""` preserves exactly the pre-088 behaviour (the deliberate escape hatch).
- **Refusal ×3** — the exact 04:00 reproduction refuses with `session not started`; the rendered row is asserted **exactly**, not by substring (B-126: `"ADR% used    — (session not started)"`); the three states (computed / day-boundary refusal / `rth_dailies_failed` fetch refusal) are pairwise distinct.
- **Boundary ×1** — one `Stage2Inputs`, `today_et` fixed, only `rth_dailies[-1]`'s own date crosses the line: refuses one bar short of today, computes the instant it is dated today. The case that produced the defect, tested directly rather than assumed.
- **Fixture ×1** — B-136, checked as code (AST import scan): no import from `test_attach.py` or `test_080_two_stage_attach.py`.
- **Divergence — deliberately absent.** Part 0 item 3 found no second basis object to diverge from the first, so there is nothing for an identity guard to check; `083`'s Divergence test has no analogue here, and inventing one would assert an object identity nothing threatens.

**Confirmed RED against pre-fix code**: `git stash push -- live/attach/attach.py live/tui/app.py`, ran the new file — 4 of 7 failed with `TypeError: Stage2Inputs.__init__() got an unexpected keyword argument 'today_et'` (the four tests that construct `Stage2Inputs(today_et=...)` directly); the escape-hatch and Fixture tests correctly still passed, since they exercise behaviour the fix does not change. `git stash pop` restored the fix; full file re-confirmed green (7 passed).

**Two existing shared fixtures needed updates**, both because they now drive a real attach through `_begin_attach`, which stamps `today_et` from the actual current date, while their own daily-bar fixtures were dated in the past (`2026-06-…`):
- `live/tests/test_attach.py::Fake.daily_bars` — stamps its last bar's `ts` to the real current ET date (`dataclasses.replace`, since `Bar` is frozen); every OTHER bar, and every direct caller of the module-level `dailies()` helper (`adr_pct(dailies())`, `atr_d14(dailies(20))`, …, none of which reads a real clock), is untouched.
- `live/tests/test_attach_is_reachable_by_key.py::FakeIB.reqHistoricalData` — same fix, one line, on the `"1 day"` branch's last `StubBar`, reusing the file's own existing `TODAY = date.today().isoformat()` constant rather than adding a second clock source.

Two tests broke on first full-suite run because of this and are now fixed: `test_attach_is_reachable_by_key.py::test_a_key_press_renders_the_context_block_not_only_the_symbol` (asserted `ADR% used` renders a number — it was rendering `session not started` because `FakeIB`'s dates never matched real "today") and `test_attaching_state.py::test_an_explicit_failure_refuses_a_row_the_baseline_does_not` (asserted the clean baseline refuses zero rows — it was refusing one, `ADR% used`, for the same reason). Both confirmed the SAME root cause (stale fixture dates, not a defect in the fix itself) before being repaired, by inspecting the rendered panel body each failure printed.

**Suite counts**: `live/` — 219 passed (was 217 passed, 2 failed on the first run before the two fixture fixes above). Full repo suite (`pytest -q`, root): **12 failed, 630 passed** — cross-checked by name against `086`'s own done-note (`handoff/done/086-for-code-task-triage-the-twelve.md`) and confirmed to be the IDENTICAL twelve pre-existing guards `086` triaged and deliberately left unfixed (`test_export_scope_is_derived`, `test_handoff_state_declared`, `test_inbound_run_record_has_no_conflicts`, both `test_observations_ledger` rows, both `test_regime_prompt_invariants` rows, `test_regime_snapshot_could_not_do`, the `test_task_file_shape` trio, `test_uat_has_a_file`) — none of them touches `attach.py`/`app.py`/anything this task changed, and this task adds zero new failures to that set. `verify.ps1` runs as the closing step regardless; see its own output, not pasted here per this task's own instruction.

---

## What was NOT touched, confirmed

`core/indicators/context.py` — byte-identical. `ADR20`'s own definition, `request_timeout_s` (B-132), the forming-bar sawtooth, the repaint path/streams/HEALTH (087's) — all untouched. **No config key** — Candidate B did not hold. The level rail's `prev_day`/`PDH`/`PDL` construction — read, found to share the same day-boundary defect (see `bugs:` `NEW` above), deliberately not fixed here.

---

## UAT

`christoph/open/048` — live, not performed here, per §6's own instruction.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here. `export-handoff.ps1`/commit/push follow, scoped to this task's own files (`live/attach/attach.py`, `live/tui/app.py`, `live/tests/test_attach.py`, `live/tests/test_attach_is_reachable_by_key.py`, `live/tests/test_088_adr_day_boundary.py`, this note) — the tree continues to hold unrelated synced content from other sessions/Drive sync (`christoph/open/043`, several `handoff/inbox/*` entries including `066`/`067`/`073`/`076`/`077`/`085`, `docs/regime-snapshots/2026-08-24.md`) left untouched, per the same discipline `083`/`087` recorded.

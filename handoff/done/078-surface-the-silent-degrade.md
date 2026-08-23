---
id: 078
title: warm() failing was invisible even when every row recovered, and the fallback never consulted the pacing guard — both fixed
type: task
class: product
story: S037
epic: 4
owner: claude-code
unblocks: NOTHING
depends: none
touches: the attach path — the warm() call site and the per-role fallback reads
uat: c041
bugs:
  - id: B-130
    action: close
    status: "Fixed. `_context_block` used to swallow `warm()`'s exception with a bare `except Exception: pass` — no trace anywhere. Now captures the reason (`_reason(exc)`) and returns it as a third value; `attach()` surfaces it via `AttachResult.partial`/`Attached.partial` — the SAME field `058` built, rendered by the SAME existing row (`context_rows()`'s `{partial} (flagged, not an error)` line, byte-for-byte unchanged) — whenever `warm()` failed, even when every individual row still measured via its own fallback and would otherwise have looked completely clean. When a row ALSO genuinely refuses, the two facts are combined in one sentence rather than one silently displacing the other."
  - id: B-133
    action: close
    status: "Fixed. `IBKRMarketData._bars` — confirmed the single choke point every per-role fallback (`daily_bars`/`today_minutes`/`intraday_sessions`/`sector_today_minutes`/`sector_sessions`) falls through to when `_warmed()` misses — now calls `self._pacing.check(_pacing_key(c), 1, now=time.monotonic())` before dispatching, exactly as `warm()`'s own gather already does. No pacing violation fired across 075's twelve live runs with the guard entirely absent here, so this closes a latent gap, not an observed one — recorded that way per the task's own instruction."
---

**Status** RUNNING

# 078 — done. Both defects fixed. Attach duration is unchanged — this task does not make anything faster, only legible.

**This note needs to be pasted to chat.**

---

## What I read at each call site, against §1's claims

**Read `handoff/done/075-attach-still-slow-measured.md` first, then the call
sites themselves, not as a substitute** (078's own instruction). Every claim
in §1 matches what the tree actually showed:

- `_context_block` (`live/attach/attach.py`): `md.warm(c)` genuinely was
  wrapped in a bare `try/except: pass` — confirmed, line-for-line.
- `IBKRMarketData._bars` (`live/attach/ibkr.py`): confirmed the single
  choke point — `daily_bars`, `today_minutes`, `intraday_sessions`,
  `sector_today_minutes`, `sector_sessions` each check `self._warmed(c,
  role)` first and fall through to `self._bars(...)` on a miss. Confirmed
  it never called `self._pacing.check(...)` anywhere, unlike `warm()`
  itself.

**One nuance worth stating plainly, since it wasn't obvious going in and
078 asks for exactly this kind of correction:** the "refusal is
distinguishable from a successful read that returned nothing" property
(exit test 2's own framing) was **already correct before this task** for
the exception case — `dailies_on()` and its siblings in `attach.py` already
catch a fallback's exception and record its SPECIFIC reason
(`_daily_failed[basis.use_rth] = _reason(exc)`), separate from the generic
`"no daily bars"` default a successful-but-empty read gets. What was
actually missing, and what made the corresponding test genuinely red before
this fix, was narrower than that framing suggested: `AttachResult.partial`
not reflecting the degraded gather at all when rows ALSO refuse for an
unrelated reason (see below) — a case of B-130, not a gap in the
already-correct refusal-reason distinction B-133's exit test names.

---

## What changed

**B-130.** `_context_block` now returns a third value, `warm_failure: str`
(the caught exception's reason, or `""`), instead of silently discarding
it. `attach()` reads it alongside the existing `refused` list and combines
both facts into `AttachResult.partial` rather than letting either silently
displace the other:

- Both true → `"{N} of {M} rows unavailable (gather degraded - {reason})"`.
- Only rows refused (the pre-existing 058 case, unchanged) →
  `"{N} of {M} rows unavailable"`.
- Only `warm()` failed, every row still measured via fallback (the new
  case 075 actually observed 3 of 6 times on AMZN) →
  `"gather degraded - {reason}"`.

**Why the combined case was necessary, not a nice-to-have**: the shared
test fixture (`Fake()`) always has PMH/PML refuse (no pre-market bars in
its default minute series), so on the FIRST attempt at this fix, `refused`
was never actually empty and the degraded-gather sentence was permanently
masked by the ordinary, unrelated refusal message. That would have meant
the exact scenario this task exists to fix — a real refusal AND a real
`warm()` failure landing together — is precisely the morning the signal
goes quiet again. Caught by the fixture forcing the question, not by
re-reading the code a second time.

**No new grammar token, no new colour, no new row** — same field
(`partial`), same render call (`context_rows()`'s
`{a.partial} ({FLAGGED_NOT_ERROR})` line, byte-identical, untouched), only
new sentences for a cause that previously produced nothing at all.

**B-133.** `IBKRMarketData._bars` now calls `self._pacing.check(_pacing_key(c),
1, now=time.monotonic())` before dispatching — the same guard, the same
instance, the same accounting `warm()`'s own gather already uses. A refusal
raised here propagates through the EXISTING exception handling in
`attach.py` unchanged (every `dailies_on`/`today_minutes`/etc. call site
already catches `_bars`'s exceptions and renders `unavailable (reason)`),
so no caller needed to change to receive it correctly.

**Chose "route the fallback through the guarded entry," not "remove the
fallback in favour of a guarded retry"** (078 §2's own fork) — this
preserves exactly what renders today (a role that can recover via fallback
still does), which is the option the task itself says is mine to make;
removing the fallback would change what renders on a name that currently
recovers, and that is explicitly not mine to decide unilaterally.

---

## Tests — all three exit tests, each seen red first

New file: `live/tests/test_078_surface_the_silent_degrade.py`, five tests.
Verified against the real pre-078 code via `git stash push --keep-index --
live/attach/attach.py live/attach/ibkr.py`:

1. `test_a_failed_warm_that_still_measures_reports_a_degraded_gather`
   (**Green**) — RED pre-fix (`r.partial` was `""`). Needed a new fixture,
   `FakeWithPremarket`, because the shared `Fake()` always leaves PMH/PML
   refused — no existing test could reach a genuinely zero-refusal attach
   to isolate this signal.
2. `test_warm_and_fallback_both_failing_refuses_with_a_specific_reason`
   (**Refusal**) — RED pre-fix, specifically on the COMBINED-message
   assertion (see the nuance above — the reason-distinguishing behaviour
   itself was already green pre-fix; the combined `partial` wording was
   not).
3. `test_the_fallback_path_consults_the_pacing_guard` (**Guard**) — RED
   pre-fix (`_pacing._seen` stayed empty after a direct `_bars()` call).
4. `test_the_fallback_path_refuses_once_the_guard_would_be_exceeded` — RED
   pre-fix (no `RuntimeError` raised at all).
5. `test_a_clean_warm_reports_no_partial_at_all` — a control, already green
   pre-fix (confirms the fix adds no noise to the ordinary case). Not one
   of the three official exit tests.

**One test-infrastructure issue found and fixed, unrelated to the
production defects**: `test_the_fallback_path_consults_the_pacing_guard`
failed intermittently depending on full-suite run order —
`RuntimeError: There is no current event loop in thread 'MainThread'`,
raised by `eventkit` (an `ib_async` dependency) reading
`asyncio.get_event_loop()` at import time. `live/tui/app.py`'s
`_attach_worker` already documents this exact class of issue and carries
an identical guard for the worker-thread case; the same guard is now
applied in the test before its first direct `_bars()` call. Not a fix to
production code — a pre-existing environmental fragility this task's new
test happened to be first to trigger in the suite.

`git stash pop` restored the fix afterward. All five green against the
current code.

---

## Attach duration is unchanged

Per §5's explicit requirement: **this task does not make the attach
faster.** Nothing about the wire-level request count, the timeout bound,
or the 20-session intraday pull (the actual dominant cost 075 measured) was
touched. The only new work on any request path is one `_PacingGuard.check()`
call per fallback request — a dict lookup and a list comprehension over a
2-second window, not a network round trip — so this is not expected to be
wall-clock-visible, and no live measurement was taken to confirm that
(075's harness was scratch and stays scratch; nothing here reruns it).

---

## Not done, per §3's explicit list

No new screen state invented. `request_timeout_s` untouched. No historical
request's size or shape changed. The attach was not restructured into
stages. No measurement harness committed — `live/tests/test_078_*.py` is a
regular behavioural test file, not scratch, and lives in the repo exactly
as every other test here does; 075's own timing harness remains at
`$env:TEMP` and is untouched by this task.

---

## Test results

`live/tests/test_078_surface_the_silent_degrade.py`: **5 passed** (new).
`live/` in full: **173 passed, 0 failed** (was 168 after `072`; +5).

---

## UAT

`christoph/open/041-for-christoph-task-uat-078-degraded-attach.md` —
live, during market hours. Not performed here, per the task's own
instruction ("Not yours to perform and not yours to mark passed").

---

## Closing sequence

`verify.ps1` runs as the last action, per §5 — not pasted or summarised
here. `export-handoff.ps1`/commit/push follow, from the main checkout,
scoped to this task's own files.

---
id: 058
title: Attach latency (worker + grouped concurrency) and the ATTACHING screen-level state
type: done-note
class: product
task: handoff/inbox/058-for-code-task-attach-latency-and-attaching-state.md
task-version: 1.0
owner: claude-code
tree: D:\Dev\momentum
promotes: OBS-041, OBS-079
---

**Status** RUNNING

# 058 — attach latency, and the ATTACHING display state

Gate checked first: `handoff/inbox/058-for-code-task-attach-latency-and-attaching-state.md`
existed and `handoff/done/058-*.md` did not, at task start.

## What this is

Christoph's ruling (2026-08-22): **worker plus grouped concurrency, atomic swap, no
progressive fill.** All four parts built, plus the two spec revisions the task's derivation
note required in the same session. One part — the live wall-clock measurement — is **owed**,
not fabricated; see "What is not done" below.

## Part 1 — collapsed the redundant daily request

`daily_bars(c, basis)` now asks for `LONG_DAILY_DURATION = "1 Y"` when `basis.use_rth` is
true (was `DAILY_DURATION = "60 D"` for both RTH and ETH). ADR%/the SMA stack/PDH-PDL are
unaffected — `adr_pct`/`sma` slice `dailies[-n:]` from the tail regardless of how long the
list is — and the same 1Y RTH series is now where `_context_block` reads 52wH/52wL/ATH
(`max`/`min` over `rth_dailies`), instead of a second `md.year_high_low(c)` round trip.
`year_high_low` is removed from the `MarketData` Protocol entirely.

Takes the underlying's historical request count from **five to four**, checked on the wire in
`live/tests/test_attach_is_reachable_by_key.py::test_a_key_press_renders_the_context_block_not_only_the_symbol`
(exactly one `1 Y` request, exactly one `60 D` request, four total) and in
`tests/test_session_basis.py::test_the_rth_daily_request_is_the_only_one_058_collapsed`.

**`tests/test_session_basis.py`'s `test_the_thirteen_do_not_share_a_request_with_anything_
038_settled` asserted the OPPOSITE of this** — that the long-range request must never share a
round trip with ADR/the SMA stack. Retired and replaced with
`test_a_long_range_request_now_shares_the_rth_daily_request` /
`test_the_rth_daily_request_is_the_only_one_058_collapsed`, which document why 058 overturns
that isolation deliberately (058 is a later, explicit product ruling; the 041/038-era test is
quoted in the new docstring rather than silently deleted).

## Part 2 — concurrent dispatch, and the pacing guard

`IBKRMarketData.warm(c)` (`live/attach/ibkr.py`) gathers every independent historical request
one attach needs — four for the underlying, six with a mapped sector ETF — via
`asyncio.gather(..., return_exceptions=True)` inside ONE round trip to the existing
`ibkr-broker` loop thread, through a new `_BrokerLoop.call_many` / `_ThreadedIB.
reqHistoricalDataMany`. `attach.py`'s `_context_block` calls `md.warm(c)` once, wrapped in
`try/except: pass`, before its existing per-role reads — each of `daily_bars`/`today_minutes`/
`intraday_sessions`/`sector_*` now checks a `self._warm` cache keyed by ROLE
(`"rth_dailies"`, `"eth_dailies"`, …) first and falls back to its own single live request if
warming did not populate it (every existing fixture across three test files never implements
`warm()` as anything but a no-op, and is unaffected — the fallback path is what they exercise).

`set(ib.threads) == {"ibkr-broker"}` (`test_the_thread_bridge_carries_a_real_async_client`)
**still passes, unmodified** — concurrent coroutines gathered on one loop satisfy it, since it
forbids a second OS thread, not concurrency within the one loop.

**The pacing guard (`_PacingGuard`, `live/attach/ibkr.py`) is built, not assumed** —
`live/tests/test_pacing_guard.py`, 9 tests. Refuses a batch that would push a
`(symbol, exchange, tick type)` key past 5 requests inside a 2-second rolling window.
**Seen red before green, per instruction**: `warm()`'s call to `self._pacing.check(...)` was
temporarily disabled, `test_warm_refuses_a_re_attach_inside_the_pacing_window` was run and
failed (`DID NOT RAISE RuntimeError`), the check was restored, and the same test passed. Not
left as a trace in the file — the demonstration is recorded here per the same instruction 057
followed for its own red-then-green demonstration.

## Part 3 — the ATTACHING state, and the atomic swap

`live/tui/app.py`: `on_input_submitted` now does the atomic swap in three steps —

1. `_begin_attach(symbol)` — drops any existing `Attached` row for that symbol from
   `record.attached` and sets `record.attaching = symbol`, synchronously, before anything
   async happens. Rendered immediately (`await self._rerender()`).
2. `self.run_worker(functools.partial(self._attach_worker, symbol), thread=True, ...)` runs
   the blocking `attach()` call **off the Textual event-loop thread** — Part 2 shrinks the
   window the freeze covers; it does not remove the freeze itself, since `attach()` still
   blocks on `future.result()` inside the gather.
3. `_attach_worker` marshals its result back to the main thread via `self.call_from_thread
   (self._finish_attach, ...)`, which clears `record.attaching` and lands every value in ONE
   `await self._rerender()` — success, refusal, or a screen-level `AttachResult.partial`
   statement ("N of M rows unavailable", rendered via `Cell.degraded(text,
   FLAGGED_NOT_ERROR)`) all in the same paint.

`grammar.py` gains `ATTACHING` — a new badge word, dim-inverse (`Cell.attaching(symbol)` →
`[ ATTACHING SYMBOL ]`), and `day_record.py` gains `DayRecord.attaching: str` and
`Attached.partial: str`.

**Five new tests**, `live/tests/test_attaching_state.py`, driven with a `threading.Event`
-blocking `MarketData` fake (never a sleep — a real OS thread runs the worker, so the block is
deterministic rather than a race):

- the screen shows `ATTACHING` and no context rows while the gather is blocked, then lands
  everything and clears the badge once released
- the UI accepts a `ctrl+tab` key press while the worker is blocked (the freeze fix, asserted
  directly rather than only inferred from the worker existing)
- re-attaching an already-attached symbol drops its old numbers the instant the new attach
  starts — never visible under the new header while the gather is in flight
- an explicit `daily` failure widens the "N of M rows unavailable" count past a clean attach's
  own baseline (which is not zero — `Fake()`'s fixture has no pre-market bars, so PMH/PML
  legitimately refuse even on an otherwise-clean attach; the test asserts the delta, not an
  absolute zero)

## Part 4 — `StartupFetch(0)`, feature-detected

`connect()` tries `from ib_async.ib import StartupFetch` and passes `fetchFields:
StartupFetch(0)` to `connectAsync` if the import succeeds; otherwise passes nothing (no shim).
Checked directly against this venv's installed `ib_async` (2.1.0) before writing the code —
`StartupFetch(0)` is a legal empty `IntFlag` and `connectAsync`/`connect` both expose the
`fetchFields` parameter.

## A latent bug this task's own worker change exposed, and fixed

Moving `attach()` off the asyncio-loop-carrying thread (Part 3) broke five tests in
`live/tests/test_attach_is_reachable_by_key.py` with `contract lookup failed (RuntimeError)`,
message `There is no current event loop in thread 'ThreadPoolExecutor-...'` (and, on a later
test, `'MainThread'`). Root cause: `ib_async`'s dependency `eventkit` calls
`asyncio.get_event_loop_policy().get_event_loop()` at **import** time
(`eventkit/util.py:24`, `main_event_loop = get_event_loop()`), and Python's default asyncio
policy raises rather than auto-creates on any thread with no loop object set. Pre-058, the
first `ib_async` import in the test process happened to occur inside an active `asyncio.run()`
call on the main thread, where `_local._loop` was already set — masking the fragility. Once
`ib_async` is first imported from a bare worker thread (or from the main thread after ANY
prior `asyncio.run()` has cleaned up and closed its loop, which sets `_set_called=True,
_loop=None` and closes the auto-create gate), the import fails, is never cached, and every
later test in the same process inherits the failure.

**Fix**: `_attach_worker` gives its own thread a loop object before calling `attach()` —
`asyncio.set_event_loop(asyncio.new_event_loop())`, guarded by a `try: asyncio.get_event_loop()
except RuntimeError` so a reused thread-pool thread does not accumulate loop objects. Never
run — `_BrokerLoop` is the loop that actually carries traffic — it exists only to satisfy
`eventkit`'s import-time check. All 18 tests in that file pass again, and this fix is what let
`ib_async` get imported and cached successfully the first time regardless of which thread does
it first, so no other test file needed a corresponding change.

## Spec revisions, in the same session per the task's derivation note

- `SPEC.md` §4: `ATTACHING` added to the canonical vocabulary and the dim-inverse badge list,
  with a dated note (2026-08-22, 058) pointing at the task's ruling.
- `SPEC.md` §6b.5: two new rows — the `ATTACHING` state (and why it is a DIFFERENT case from
  the existing `STALE`-on-detach row, not a variant of it), and the screen-level partial-attach
  statement.
- `BUILD-PLAN.md` §3 (S010): `fetching dailies…` removed from the rendered states; a note
  explains it contradicted the slice's own §7 (*"fetched or `unavailable (reason)`. There is
  no third state"*) and that §7 wins, pointing at the one screen-level `ATTACHING` state as
  what actually renders during the gather.
- `config/ibkr.yaml`'s `request_timeout_s` note updated to record that both halves of "the
  real fix" it deferred (worker + concurrent dispatch) landed under 058; the value itself is
  unchanged.

## Observations ledger

`OBS-041` and `OBS-079` promoted, each with a `resolution:` entry appended to `## Resolutions`
in `docs/observations/OBSERVATIONS.md` (table rows' `status` column also changed `OPEN` ->
`PROMOTED`). `OBS-079`'s resolution corrects its own caveat: it warned a naive `gather()` of
"up-to-six per-symbol requests" sits at the six-request pacing edge — after Part 1's collapse
the underlying carries **four**, not six, so the gather has genuine headroom rather than
sitting at the edge.

**`tests/test_observations_ledger.py`'s 7 resolution/status tests pass against this edit**
(checked directly: `pytest tests/test_observations_ledger.py -k "resolution or status or
review_by or review_date"`, 7 passed). The file's own 2 pre-existing failures
(`test_every_retired_uat_has_a_register_row`, `test_refusal_b_a_retired_uat_with_no_
destination_is_red`) are unrelated and predate this session (confirmed by `git stash`-ing this
task's changes and re-running — identical failures against `main` at the pre-058 HEAD).

**This edit is NOT committed as part of this task**, and that is deliberate, not an oversight
— see "A concurrent session, and what it changed about how this closes" below.

## What is not done — Part 5's live measurement

**Blocked by TWS being unreachable partway through this session, not by anything code-side.**
Port 7496 was open and answering at session start (checked directly before any work began).
A measurement script (`$env:TEMP\...\measure_attach_058.py` — scratch only, never the repo,
readonly connection, `client_id=58` to avoid any collision with the app's `client_id=7`, 021's
121, or 019's 11) was written to attach QQQ (liquid large-cap) and CULP (thin small-cap, same
symbol S010's own UAT used) three times each, 16s apart to clear `COOLDOWN_S`. Run: `API
connection failed: ConnectionRefusedError ... Make sure API port on TWS/IBG is open`. Rechecked
all four broker ports (7496/7497/4001/4002) directly by socket — all four timed out, not merely
refused, meaning TWS itself was no longer running, not just declining this client id.

**No number is reported here in its place.** Fabricating or estimating a "before/after" figure
would be exactly the well-formed-value-answering-a-different-question defect this project
exists to prevent. What IS established without a live connection: the request COUNT collapsed
from 5 to 4 (checked on the wire against fixtures, Part 1) and from 7 sequential round trips to
1 gathered round trip for a sector-mapped symbol (Part 2, `test_warm_dispatches_six_requests_
for_a_symbol_with_a_sector`). The wall-clock consequence of that is real but unmeasured this
session.

**Owed to whoever picks this up next**: re-run `measure_attach_058.py`'s method (or rewrite it
fresh — nothing in it depends on this session) once TWS is confirmed listening on 7496, and
report the actual before/after figures. `OBS-041`'s own promotion above already documents this
gap; no new observation row is needed for it.

## A concurrent session, and what it changed about how this closes

**A second live session was working in this same tree for at least part of this task**,
confirmed by its own finding: `docs/observations/OBSERVATIONS.md` (working tree, uncommitted)
carries a new row, `OBS-081`, that this session did not write, naming this task's own files
(`attach.py`, `ibkr.py`, `app.py`, `day_record.py`, `grammar.py`, three test files, plus a new
`test_pacing_guard.py`) as unfamiliar paths it correctly identified as another session's WIP
and correctly did not touch. `git diff --cached --name-only` confirms the other session had
already staged (not committed) four files before this task's own closing sequence began:
`docs/observations/OBSERVATIONS.md`, `handoff/done/062-tws-order-test-instrument.md`,
`handoff/inbox/062-for-code-task-tws-order-test-instrument.md`, `verify.ps1` — all task 062's,
none of which this session created or intended to commit.

**Consequence for this task's own OBS-041/OBS-079 promotion**: those edits are real, in the
working tree, and pass their own tests (see above) — but `docs/observations/OBSERVATIONS.md`
cannot be committed by this session without EITHER discarding the other session's staged
`OBS-081` row OR committing it under this task's message despite this session not having
written it. Neither is acceptable, so this task's commit **excludes** that one file. It is left
exactly as found: staged content from `062`, plus this session's own edits layered on top in
the working tree, unstaged, for whichever session runs `git add`/`git commit` on it next to
resolve. `verify.ps1`, `export-run-record.md`, `sync-run-record.md` and the two `062` handoff
files are likewise untouched and uncommitted by this session, for the same reason.

**031 (a lease file and pre-commit/pre-push hooks) is the settling mechanism for exactly this,
and it is unbuilt** — `OBS-081` says so directly. Not this task's to build; recorded here as a
second, independent sighting of the same gap.

## Also found, not fixed here

`sync.ps1` (run once, at the start of this session's closing sequence, per the standing
convention) exited 1: three `handoff/inbox/` files differ between Drive and the repo copy
(`040-for-code-task-readonly-stop-and-accounting-probe.md`,
`043-for-code-task-third-pair-and-two-instruments.md`,
`052-for-code-task-product-spec-pointer.md`). Nothing was overwritten, per the tool's own
design. **Which side is authoritative is a judgment call this task has no basis to make** —
unrelated to attach latency, pre-existing, and left for a session that can read both sides'
provenance.

## Exit tests

**Green.** `verify.ps1` ran from the main checkout, HEAD `8be92f8` at that point, at
2026-08-23 07:58:43 +02:00. Section 1: `12 failed, 546 passed, 1 warning in 144.94s` — the
12 named failures are pre-existing and unrelated (confirmed above); every test this task added
or touched is among the 546. Section 10 (tws_order, added by the concurrent `062` session):
`37 passed`.

- Attach a liquid large-cap, a thin small-cap, a name with no sector mapping — all three exit
  through `attach()`'s existing fixture suite (`live/tests/test_attach.py`,
  `test_qqq_2026_08_13_regression.py`) plus the new `test_attaching_state.py`; every field is a
  number or a named refusal.
- The one-loop thread test passes, unmodified.
- The pacing guard passes, and was seen red first (documented above).
- The collapsed daily fetch serves both the tail-consumers and 52wH/52wL — checked on the wire,
  not only asserted in prose.

**Refusal.**
- Kill the network mid-attach: covered by `Fake(fail=[...])` fixtures and
  `test_an_explicit_failure_widens_the_unavailable_count` — the completed screen carries named
  refusals plus the screen-level "N of M rows unavailable" statement, never a partial ADR.
- Same symbol twice inside 15s: `test_refusal_b_the_same_symbol_twice_inside_the_cooldown`,
  unmodified, still passes.
- No sector mapping: `test_refusal_c_end_to_end_no_sector_means_rvol_rel_refuses_by_name`,
  unmodified, still passes.
- UI stays responsive during attach: `test_the_ui_stays_responsive_during_an_attach`, new.

**UAT — Christoph.** Not authored here as a `christoph/open/` file — this task's own inbox
entry names no UAT destination and `NOW.md`'s exit table convention (per `053`) allows `UAT |
... | None` as a valid declaration when genuinely owed elsewhere; the live-attach reading this
task's own UAT section calls for depends on Part 5's measurement, which is blocked (see
above). Once TWS is reachable and Part 5 is measured, the three UAT items in the task file
(read the screen during a real attach; attach with TWS disconnected; the screen-could-be
-mistaken-for-complete question) are still owed and should be authored as a `christoph/open/`
file at that point — not now, against numbers that do not exist yet.

## Closing sequence

`sync.ps1` (exit 1, three pre-existing differing files, documented above — not this task's) →
work → `verify.ps1` (green modulo the 12 pre-existing failures, documented above) → this
done-note. **Export and push are the two steps this session did NOT run**, and that is
deliberate: `export-handoff.ps1` copies `handoff/` recursively, which would carry the
concurrent session's uncommitted `062` files nowhere (export only ever touches tracked,
committed content reachable from `git`, so this is actually safe) — the real reason is that
committing first, narrowly, is what has to happen before an export or a push means anything,
and this session's commit deliberately excludes the four files the other session already
staged. **Recommended next step for whoever resumes this tree**: commit this task's own files
(the list below), then decide with the other session (or Christoph) how
`docs/observations/OBSERVATIONS.md` / `verify.ps1` / the `062` handoff files should be
committed, then run `export-handoff.ps1` and push once both are settled.

Files this task's own commit should cover, and only these:
`config/ibkr.yaml`, `docs/specs/BUILD-PLAN.md`, `docs/specs/SPEC.md`, `live/attach/attach.py`,
`live/attach/ibkr.py`, `live/tests/test_attach.py`,
`live/tests/test_attach_is_reachable_by_key.py`, `live/tests/test_attaching_state.py`
(new), `live/tests/test_pacing_guard.py` (new), `live/tests/test_qqq_2026_08_13_regression.py`,
`live/tui/app.py`, `live/tui/day_record.py`, `live/tui/grammar.py`, `tests/test_session_basis.py`,
and this done-note itself.

---

**This needs to be pasted to chat.** Per the handoff convention, chat cannot see this repo —
writing it here is not the same as it being read. **In particular: Part 5's live measurement is
owed, and the concurrent-session situation with `docs/observations/OBSERVATIONS.md` needs a
person's attention** — both are things chat cannot discover on its own from a stale `RUNNING`
status.

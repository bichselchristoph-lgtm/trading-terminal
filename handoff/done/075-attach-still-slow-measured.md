---
id: 075
title: A symbol switch takes over twenty seconds — measured live, not fixed. warm() timed out and silently fell back on half the AMZN attaches
type: task
class: product
story: S037
epic: 4
owner: claude-code
unblocks: NOTHING
depends: none
touches: the attach path, instrumentation only in Part 0
bugs:
  - id: NEW
    action: raise
    status: "CONFIRMED FIRING LIVE, not hypothetical. `_context_block`'s `md.warm(c)` call is wrapped in a bare `try/except: pass`; on any exception every per-role read (`daily_bars`/`today_minutes`/`intraday_sessions`/`sector_today_minutes`/`sector_sessions`) falls back to its own individual, SEQUENTIAL live request via `IBKRMarketData._bars` — the single choke point every fallback goes through, confirmed by direct instrumentation, and confirmed to never consult `_PacingGuard`. In this session's 12 live runs, `warm()` raised `TimeoutError: no answer in 60s (request_timeout_s)` on 3 of 6 AMZN-involving attaches (`first_AMZN_1`, `switch_2_to_AMZN`, `switch_3_to_AMZN`) — each of those three then re-issued up to 5 MORE historical requests sequentially, one at a time, adding 70-83 more seconds on top of the 60s the failed gather already spent. This is the exact pre-058 sequential shape, reintroduced silently, live, roughly half the time on the slower symbol. Nothing on screen or in any log line said the fast path had failed — the panel just took longer. Raised regardless of whether it is THE cause of the 20s+ report (see below — it plausibly is, on the attaches where it fired, and it is a defect on its own terms per the task's own instruction either way)."
---

**Status** RUNNING

# 075 — done. Measured, not fixed. warm() times out and silently degrades to the pre-058 sequential path on roughly half the AMZN attaches; the dominant single cost on EVERY attach, warmed or not, is one specific request — the 20-session 1-minute intraday pull.

**This note needs to be pasted to chat.**

---

## Discipline this note holds to, stated up front

**Every run reported individually below — none of the numbers in this note
are a mean.** First attach and switch are two separate sections. **No
optimisation was applied anywhere in this task.** Where a one-line fix looks
obvious (§below), it is named and left undone.

---

## Part 0 — connection facts

Live TWS, `127.0.0.1:7496` (the real account — 7497/4001/4002 all closed,
checked by direct socket probe before connecting and again immediately
before the run started). `client_id=75` — task 075's own id, distinct from
the app's configured `7`, `021`'s `121`, and `019`'s `11`, following `058`'s
own precedent for exactly this kind of measurement script. Connection:
`connected · client 75 · read-only`. **Held for the entire run** — all 12
attaches plus the connect/instrument preamble completed; no drop, unlike
`058`'s own attempt. Harness: `C:\Users\chbic\AppData\Local\Temp\
075_attach_timing.py` (scratch, not committed — see "Instrumentation
permanence" below). Full raw log also written to `C:\Users\chbic\AppData\
Local\Temp\075_attach_timing_output.txt`.

Every wrap is a monkeypatch on the connected instance (`broker._ib`,
`broker.md`) or the `MomentumApp`/`ib_async` classes before construction —
**no source file in the repository was edited to take this measurement.**
Reviewed by a Plan-agent pass before any live connection was opened, which
caught two real gaps in the first draft: cooldown spacing needed to be
polled per-symbol (`md.cooldown_remaining_s`) rather than hand-timed sleeps
(AMZN has its own repeats too, not just QQQ), and `open_tick_stream`
unconditionally raises in this slice — there is no live tick-subscription
mechanism to measure a release cost against, so that question is answered
N/A rather than measured.

---

## Summary — every run, individually, no averaging

| Run | Total (keypress→paint) | `warm()` outcome | Wire historical-data calls | Fallback fired? |
|---|---:|---|---:|---|
| `first_QQQ_1` | **15.81s** | succeeded | 3 | no |
| `first_QQQ_2` | **47.91s** | succeeded | 3 | no |
| `first_QQQ_3` | **32.15s** | succeeded | 3 | no |
| `first_AMZN_1` | **143.18s** | **TIMED OUT (60.005s)** | 5 (warm) + 5 (fallback) = 10 | **yes, all 5 roles** |
| `first_AMZN_2` | **60.78s** | succeeded (59.99s, at the edge) | 5 | no |
| `first_AMZN_3` | **60.78s** | succeeded (59.99s, at the edge) | 5 | no |
| `switch_1_attach_QQQ` | **54.45s** | succeeded | 3 | no |
| `switch_1_to_AMZN` | **60.59s** | succeeded (59.99s, at the edge) | 5 | no |
| `switch_2_attach_QQQ` | **37.23s** | succeeded | 3 | no |
| `switch_2_to_AMZN` | **143.44s** | **TIMED OUT (60.011s)** | 5 (warm) + 5 (fallback) = 10 | **yes, all 5 roles** |
| `switch_3_attach_QQQ` | **52.73s** | succeeded | 3 | no |
| `switch_3_to_AMZN` | **130.56s** | **TIMED OUT (60.011s)** | 5 (warm) + 5 (fallback) = 10 | **yes, all 5 roles** |

**Every QQQ attach (no sector ETF) made exactly 3 historical requests.**
**Every AMZN attach (sector ETF resolved live to `XLC`) made exactly 5 when
`warm()` succeeded, and up to 10 when it didn't** — matching 058's own "3 /
5" claim exactly on the count, and directly measuring what a `warm()`
failure costs beyond that claim.

**No pacing-guard firing observed in any of the 12 runs** — no `RuntimeError`
naming "pacing limit" anywhere in the log.

---

## First attach — QQQ (3 runs, full detail)

`warm()` succeeded every time; no fallback ever fired for QQQ. The entire
duration in all three runs is inside `warm_total`, and inside `warm_total`
it is overwhelmingly the **20-session 1-minute intraday request** (the RVOL
reference) — the 1-year daily and today's-minutes requests are consistently
fast (well under 2s each).

**`first_QQQ_1` — 15.8112s total.**
`resolve` 0.238s · `warm_total` 15.2245s, of which: `1 Y`/`1 day` daily
0.7068s, `1 D`/`1 min` today 1.9219s, **`20 D`/`1 min` intraday 15.0744s**
(the whole run's duration, essentially). `finish_attach` 0.0071s. Segments
1/2/3/5 (begin_attach, rerender, worker dispatch, finish) each ≤0.04s.

**`first_QQQ_2` — 47.9126s total.**
`resolve` 0.2342s · `warm_total` 47.3863s, of which: daily 0.7049s, today
1.4509s, **intraday `20 D` 47.2338s.**

**`first_QQQ_3` — 32.1542s total.**
`resolve` 0.2407s · `warm_total` 31.5357s, of which: daily 0.7055s, today
1.4362s, **intraday `20 D` 31.4172s.**

**The same request, the same symbol, three consecutive measurements: 15.1s,
47.2s, 31.4s.** Nothing else in the QQQ path varies meaningfully between
runs — this one request's own wall-clock time IS the variance.

---

## First attach — AMZN (3 runs, full detail)

AMZN resolves a sector ETF (`XLC`, live) — 5 requests when `warm()`
completes.

**`first_AMZN_1` — 143.1779s total. `warm()` TIMED OUT.**
`resolve` 0.2488s. `warm_total` ran 60.0052s and raised `TimeoutError: no
answer in 60s (request_timeout_s)`. The gather's own wire calls: AMZN 1Y
daily 0.7035s, AMZN 1D today 0.9663s, XLC 1D today 1.4195s, then AMZN `20 D`
and XLC `20 D` each logged at exactly ~60.005s (the bound). **Every one of
the 5 roles then fell back individually**, sequentially: `daily_bars`
(fallback) 0.9317s, `today_minutes` 0.7301s, `intraday_sessions` (AMZN `20
D`) 31.3059s, `sector_sessions` (XLC `20 D`) 48.8773s, `sector_today_minutes`
(XLC today) 0.7156s. **60.0s (failed gather) + 0.93 + 0.73 + 31.3 + 48.9 +
0.72 ≈ 143.2s — the fallback path alone accounts for roughly 83 of this
run's 143 seconds.**

**`first_AMZN_2` — 60.7821s total. `warm()` succeeded, at the edge.**
`resolve` 0.2343s. `warm_total` 60.1673s, no exception — but its own
constituent wire calls show AMZN `20 D` at 57.1017s and XLC `20 D` at
59.9939s, both a hair under the 60s bound. All `role_*` reads show `0.0s`
(true cache hits) — the fallback did not fire this time, but only barely.

**`first_AMZN_3` — 60.7820s total. `warm()` succeeded, at the edge.**
Same shape: `warm_total` 60.1609s, AMZN `20 D` 54.5689s, XLC `20 D`
59.9949s. Cache hits throughout, no fallback.

**Three consecutive AMZN first-attaches: one timed out and fell back
(143.2s), two succeeded within a whisker of the same 60-second bound
(60.8s each).** The 60-second `request_timeout_s` is not a comfortable
margin here — it is the number these requests are actually landing on top
of, not safely under.

---

## Switch — QQQ → AMZN (3 pairs, full detail)

**This is the scenario Christoph reported.** Each pair: attach QQQ, then —
deliberately not spaced — attach AMZN, to confirm the switch itself and
that AMZN's cooldown gate is independent of QQQ's.

**Pair 1.** `switch_1_attach_QQQ` 54.4455s (`warm_total` 53.8004s, all in
the `20 D` intraday request: 53.6818s). `switch_1_to_AMZN` 60.5851s
(`warm()` succeeded at the edge again — `20 D` AMZN 59.9962s, XLC 59.9963s,
`warm_total` 60.0087s, no exception, cache hits, no fallback).
**Combined QQQ-then-AMZN wall clock for this pair: 115.03s.**

**Pair 2.** `switch_2_attach_QQQ` 37.2345s. `switch_2_to_AMZN` 143.4440s —
**`warm()` timed out** (`TimeoutError`, 60.011s); the underlying AMZN and
XLC `20 D` wire calls in the gather themselves show `exc: 'CancelledError'`
this time (the two other AMZN runs' failed 20D calls did not report a
CancelledError explicitly — this one did, live evidence the gather's
in-flight requests get cancelled out from under it when the overall timeout
fires, not merely abandoned). Fallback fired for all 5 roles again: 0.71 +
0.72 + 44.15 + 36.46 + 0.72 ≈ 82.8s on top of the 60s failed gather.
**Combined pair: 180.68s.**

**Pair 3.** `switch_3_attach_QQQ` 52.7324s. `switch_3_to_AMZN` 130.5630s —
**`warm()` timed out** again (60.011s), fallback fired for all 5 roles:
0.92 + 0.75 + 35.90 + 31.11 + 1.15 ≈ 69.8s on top of the 60s failed gather.
**Combined pair: 183.30s.**

**Confirmed directly: AMZN's attach was never gated by QQQ's 15-second
cooldown** — no `COOLDOWN_WAIT` log entry appears between any
`switch_N_attach_QQQ` and its paired `switch_N_to_AMZN`, because
`cooldown_remaining_s("AMZN")` was already 0 by the time each check ran (a
different contract, keyed independently, exactly as designed). Worth
noting as a measurement artefact rather than a finding about the cooldown
itself: **because every attach in this session took 15+ seconds on its own,
same-symbol cooldown spacing was never actually the limiting factor** — by
the time a repeat QQQ attach came around, 15 real seconds had already
elapsed regardless. No `COOLDOWN_WAIT` rows appear anywhere in the full log.

---

## Establish-by-measurement checklist (§3–§4 of the task)

- **Does `warm()` complete or raise?** Both, roughly evenly on AMZN: 3 of 6
  AMZN-involving attaches raised `TimeoutError: no answer in 60s
  (request_timeout_s)`; the other 3 completed within 0.01-6s of that same
  60s bound. **Every QQQ attach completed** (QQQ's own slowest single
  request, in these runs, topped out at 53.7s — under the bound, but not by
  a wide margin either).
- **Are per-role fallback requests firing?** Yes, on exactly the 3 runs
  where `warm()` timed out, and on those runs ALL FIVE roles fell back, not
  a subset.
- **How many historical requests does one switch actually make?** 3 for
  QQQ, always. 5 for AMZN when `warm()` succeeds; **10 when it does not**
  (the gather's own 5, some completing/some cancelled, plus 5 more
  sequential fallback calls) — confirmed on the wire, not assumed from
  058's count.
- **Does the pacing guard fire?** No — not once across 12 runs.
- **Does the 15s same-contract cooldown correctly not apply to a different
  symbol?** Confirmed yes, directly (see above).
- **Cost of `asyncio.new_event_loop()`?** The call itself is effectively
  free (0.0s every time it fired). **It does NOT fire once per attach** —
  it fired 6 times across 12 attaches (on `first_QQQ_1`,
  `switch_1_attach_QQQ`, `switch_1_to_AMZN`, `switch_2_to_AMZN`,
  `switch_3_attach_QQQ`, `switch_3_to_AMZN`), each on a distinctly-named
  worker thread (`asyncio_0` through `asyncio_5`) — Textual is reusing
  pooled worker threads on the other 6 attaches, exactly as the Plan-agent
  review cautioned not to assume either way.
- **Is the old tick subscription released before the new one opens, and
  what does that cost?** **N/A.** `IBKRMarketData.open_tick_stream`
  unconditionally raises `RuntimeError("tape not opened by S010 - no tape
  components in core")` — there is no tick-subscription open/release
  mechanism in this slice at all to measure a cost against. This is a fact
  about the current slice (S010 never built tape components in core), not
  a new defect.
- **The 1Y daily request — count vs. duration** (§4's own framing): the
  1-year daily request is consistently the FASTEST of the three/five wire
  calls in every single run (0.7-1.9s, no exceptions) — **it is not where
  the time goes.** The dominant cost, on every attach regardless of symbol
  or outcome, is the 20-session 1-minute intraday request (and its sector
  counterpart for AMZN) — see below.

---

## The bottleneck, stated as what was measured, not as a diagnosis

**On every single run in this session — all 12, warmed or fallback,
timed-out or not — the dominant cost is the 20-session, 1-minute-bar
intraday request** (`INTRADAY_DURATION`/`"20 D"`/`"1 min"`, the RVOL
reference `intraday_sessions()`/`sector_sessions()` reads). It ranged from
15.1s to 60.0s+ across these runs, for both QQQ and AMZN, and for AMZN's
sector ETF XLC equally. The 1-year daily request and the one-day-of-minutes
request are both fast and consistent throughout (under 2s, every time,
every symbol). **This one request is not a hypothesis — it is what the wire
timing shows, twelve times, without exception.**

**No optimisation was applied.** If this task's own remit had permitted a
fix, the obvious next question — not answered here — would be whether that
request's size (20 sessions × 1-minute bars, ETH) can be reduced, or
whether it is inherently this slow against IBKR's historical-data service
independent of anything this codebase controls. That question is reported,
not investigated further, per §1's explicit instruction.

---

## No fix applied

Nothing in `live/attach/attach.py`, `live/attach/ibkr.py`, or `live/tui/
app.py` was changed by this task. The silent-`warm()`-failure fallback
(raised above as a bug row) is reported, not patched — even though, once
observed live, the fix shape is fairly legible (stop swallowing the
exception silently; or make the fallback consult `_PacingGuard` too; or
surface the degraded state on screen the way `AttachResult.partial` already
surfaces a partial gather). None of that is applied here, per the task's own
explicit and repeated instruction.

---

## Instrumentation permanence

**Scaffolding. Stays at `C:\Users\chbic\AppData\Local\Temp\
075_attach_timing.py`. Nothing from it enters the repository.** It answers
one measurement question with a purpose-built harness (wire-level
monkeypatches, cooldown polling, a scripted 12-run sequence) that has no
ongoing job once this task closes. The one figure that plausibly IS worth
the terminal always knowing — total attach duration, `0_TOTAL_keypress_to_
paint` — is a real candidate for a small, separate, deliberately-scoped
addition to `_finish_attach`/the record, but that is a different, smaller
piece of work than this harness, and is not built here.

---

## Full raw log (every segment, every run, verbatim)

```
{'segment': 'EVENT_LOOP_CREATED', 'run': 'unset', 'start': 924327.3151967, 'end': 924327.315197, 'dur_s': 0.0, 'detail': 'call #1 on thread MainThread', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_QQQ_1', 'start': 924329.8277, 'end': 924329.8277, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_1', 'start': 924329.8277, 'end': 924329.8324, 'dur_s': 0.0048, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_QQQ_1', 'start': 924329.8324, 'end': 924329.833, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'first_QQQ_1', 'start': 924329.8330127, 'end': 924329.8330129, 'dur_s': 0.0, 'detail': 'call #2 on thread asyncio_0', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_QQQ_1', 'start': 924329.834, 'end': 924330.0718, 'dur_s': 0.2378, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'first_QQQ_1', 'start': 924329.8339, 'end': 924330.0718, 'dur_s': 0.238, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_1', 'start': 924330.0721, 'end': 924330.7788, 'dur_s': 0.7068, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_1', 'start': 924330.0722, 'end': 924331.9941, 'dur_s': 1.9219, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_1', 'start': 924330.0723, 'end': 924345.1467, 'dur_s': 15.0744, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_QQQ_1', 'start': 924330.0719, 'end': 924345.2963, 'dur_s': 15.2245, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_QQQ_1', 'start': 924345.2963, 'end': 924345.2963, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_QQQ_1', 'start': 924345.2964, 'end': 924345.2964, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_QQQ_1', 'start': 924345.2966, 'end': 924345.2994, 'dur_s': 0.0028, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_1', 'start': 924345.3066, 'end': 924345.3137, 'dur_s': 0.0071, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_QQQ_1', 'start': 924345.3065, 'end': 924345.3137, 'dur_s': 0.0071, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_QQQ_1', 'start': 924329.833, 'end': 924345.3139, 'dur_s': 15.4809, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_QQQ_1', 'start': 924329.5393, 'end': 924345.3505, 'dur_s': 15.8112, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_QQQ_2', 'start': 924347.1017, 'end': 924347.1017, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_2', 'start': 924347.1017, 'end': 924347.1067, 'dur_s': 0.005, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_QQQ_2', 'start': 924347.1068, 'end': 924347.1073, 'dur_s': 0.0006, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_QQQ_2', 'start': 924347.1076, 'end': 924347.3415, 'dur_s': 0.2338, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'first_QQQ_2', 'start': 924347.1074, 'end': 924347.3416, 'dur_s': 0.2342, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_2', 'start': 924347.3419, 'end': 924348.0467, 'dur_s': 0.7049, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_2', 'start': 924347.342, 'end': 924348.7929, 'dur_s': 1.4509, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_2', 'start': 924347.3421, 'end': 924394.5758, 'dur_s': 47.2338, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_QQQ_2', 'start': 924347.3416, 'end': 924394.7279, 'dur_s': 47.3863, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_QQQ_2', 'start': 924394.7279, 'end': 924394.7279, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_QQQ_2', 'start': 924394.7281, 'end': 924394.7281, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_QQQ_2', 'start': 924394.7283, 'end': 924394.7313, 'dur_s': 0.003, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_2', 'start': 924394.738, 'end': 924394.7453, 'dur_s': 0.0074, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_QQQ_2', 'start': 924394.7379, 'end': 924394.7453, 'dur_s': 0.0074, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_QQQ_2', 'start': 924347.1074, 'end': 924394.7457, 'dur_s': 47.6383, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_QQQ_2', 'start': 924346.8614, 'end': 924394.774, 'dur_s': 47.9126, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_QQQ_3', 'start': 924396.5558, 'end': 924396.5559, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_3', 'start': 924396.5559, 'end': 924396.5605, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_QQQ_3', 'start': 924396.5605, 'end': 924396.5611, 'dur_s': 0.0006, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_QQQ_3', 'start': 924396.5612, 'end': 924396.8016, 'dur_s': 0.2404, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'first_QQQ_3', 'start': 924396.5611, 'end': 924396.8017, 'dur_s': 0.2407, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_3', 'start': 924396.802, 'end': 924397.5075, 'dur_s': 0.7055, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_3', 'start': 924396.8021, 'end': 924398.2384, 'dur_s': 1.4362, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_QQQ_3', 'start': 924396.8022, 'end': 924428.2194, 'dur_s': 31.4172, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_QQQ_3', 'start': 924396.8018, 'end': 924428.3375, 'dur_s': 31.5357, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_QQQ_3', 'start': 924428.3375, 'end': 924428.3375, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_QQQ_3', 'start': 924428.3376, 'end': 924428.3376, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_QQQ_3', 'start': 924428.3378, 'end': 924428.3402, 'dur_s': 0.0024, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_QQQ_3', 'start': 924428.3468, 'end': 924428.3855, 'dur_s': 0.0387, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_QQQ_3', 'start': 924428.3467, 'end': 924428.3855, 'dur_s': 0.0388, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_QQQ_3', 'start': 924396.5611, 'end': 924428.3858, 'dur_s': 31.8247, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_QQQ_3', 'start': 924396.2696, 'end': 924428.4238, 'dur_s': 32.1542, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_AMZN_1', 'start': 924430.252, 'end': 924430.252, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_1', 'start': 924430.2521, 'end': 924430.2566, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_AMZN_1', 'start': 924430.2566, 'end': 924430.2572, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_AMZN_1', 'start': 924430.2573, 'end': 924430.5059, 'dur_s': 0.2485, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'first_AMZN_1', 'start': 924430.2572, 'end': 924430.506, 'dur_s': 0.2488, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924430.5062, 'end': 924431.2097, 'dur_s': 0.7035, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924430.5064, 'end': 924431.4726, 'dur_s': 0.9663, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924430.5067, 'end': 924431.9261, 'dur_s': 1.4195, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_AMZN_1', 'start': 924430.506, 'end': 924490.5112, 'dur_s': 60.0052, 'detail': '', 'exc': 'TimeoutError: no answer in 60s (request_timeout_s)'}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924430.5064, 'end': 924490.5117, 'dur_s': 60.0053, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924430.5067, 'end': 924490.5119, 'dur_s': 60.0052, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924490.5121, 'end': 924491.4425, 'dur_s': 0.9304, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'first_AMZN_1', 'start': 924490.5113, 'end': 924491.443, 'dur_s': 0.9317, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_AMZN_1', 'start': 924490.5112, 'end': 924491.443, 'dur_s': 0.9317, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924491.4432, 'end': 924492.1677, 'dur_s': 0.7245, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'first_AMZN_1', 'start': 924491.4431, 'end': 924492.1732, 'dur_s': 0.7301, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_AMZN_1', 'start': 924491.443, 'end': 924492.1732, 'dur_s': 0.7301, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924492.1735, 'end': 924523.3642, 'dur_s': 31.1907, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'first_AMZN_1', 'start': 924492.1733, 'end': 924523.4767, 'dur_s': 31.3034, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_AMZN_1', 'start': 924492.1733, 'end': 924523.4792, 'dur_s': 31.3059, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924523.4851, 'end': 924572.2753, 'dur_s': 48.7901, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'first_AMZN_1', 'start': 924523.4849, 'end': 924572.3598, 'dur_s': 48.8749, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_AMZN_1', 'start': 924523.4849, 'end': 924572.3621, 'dur_s': 48.8773, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'first_AMZN_1', 'start': 924523.4849, 'end': 924572.3621, 'dur_s': 48.8773, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_1', 'start': 924572.3627, 'end': 924573.0734, 'dur_s': 0.7107, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'first_AMZN_1', 'start': 924572.3622, 'end': 924573.0777, 'dur_s': 0.7155, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_AMZN_1', 'start': 924572.3622, 'end': 924573.0777, 'dur_s': 0.7155, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'first_AMZN_1', 'start': 924572.3622, 'end': 924573.0777, 'dur_s': 0.7156, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_1', 'start': 924573.0871, 'end': 924573.0942, 'dur_s': 0.0071, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_AMZN_1', 'start': 924573.087, 'end': 924573.0942, 'dur_s': 0.0072, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_AMZN_1', 'start': 924430.2572, 'end': 924573.0944, 'dur_s': 142.8373, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_AMZN_1', 'start': 924429.9465, 'end': 924573.1243, 'dur_s': 143.1779, 'detail': 'AMZN', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_AMZN_2', 'start': 924574.9438, 'end': 924574.9438, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_2', 'start': 924574.9439, 'end': 924574.9484, 'dur_s': 0.0045, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_AMZN_2', 'start': 924574.9484, 'end': 924574.9489, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_AMZN_2', 'start': 924574.9491, 'end': 924575.1831, 'dur_s': 0.2339, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'first_AMZN_2', 'start': 924574.9489, 'end': 924575.1832, 'dur_s': 0.2343, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_2', 'start': 924575.1835, 'end': 924577.0507, 'dur_s': 1.8672, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_2', 'start': 924575.1836, 'end': 924577.0783, 'dur_s': 1.8947, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_2', 'start': 924575.1839, 'end': 924581.7023, 'dur_s': 6.5184, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_2', 'start': 924575.1837, 'end': 924632.2854, 'dur_s': 57.1017, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_2', 'start': 924575.1839, 'end': 924635.1778, 'dur_s': 59.9939, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_AMZN_2', 'start': 924575.1832, 'end': 924635.3505, 'dur_s': 60.1673, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_AMZN_2', 'start': 924635.3506, 'end': 924635.3506, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_AMZN_2', 'start': 924635.3507, 'end': 924635.3507, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_AMZN_2', 'start': 924635.3508, 'end': 924635.354, 'dur_s': 0.0031, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'first_AMZN_2', 'start': 924635.3621, 'end': 924635.3621, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'first_AMZN_2', 'start': 924635.3621, 'end': 924635.3621, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_2', 'start': 924635.3633, 'end': 924635.372, 'dur_s': 0.0088, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_AMZN_2', 'start': 924635.3632, 'end': 924635.372, 'dur_s': 0.0089, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_AMZN_2', 'start': 924574.9489, 'end': 924635.3723, 'dur_s': 60.4234, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_AMZN_2', 'start': 924574.6266, 'end': 924635.4087, 'dur_s': 60.7821, 'detail': 'AMZN', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'first_AMZN_3', 'start': 924637.2587, 'end': 924637.2587, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_3', 'start': 924637.2587, 'end': 924637.2633, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'first_AMZN_3', 'start': 924637.2633, 'end': 924637.2638, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'first_AMZN_3', 'start': 924637.264, 'end': 924637.4965, 'dur_s': 0.2324, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'first_AMZN_3', 'start': 924637.2638, 'end': 924637.4965, 'dur_s': 0.2327, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_3', 'start': 924637.4968, 'end': 924638.1959, 'dur_s': 0.6991, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_3', 'start': 924637.497, 'end': 924638.9347, 'dur_s': 1.4377, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_3', 'start': 924637.4972, 'end': 924640.15, 'dur_s': 2.6528, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_3', 'start': 924637.497, 'end': 924692.0659, 'dur_s': 54.5689, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'first_AMZN_3', 'start': 924637.4972, 'end': 924697.4921, 'dur_s': 59.9949, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'first_AMZN_3', 'start': 924637.4966, 'end': 924697.6575, 'dur_s': 60.1609, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'first_AMZN_3', 'start': 924697.6575, 'end': 924697.6575, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'first_AMZN_3', 'start': 924697.6576, 'end': 924697.6576, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'first_AMZN_3', 'start': 924697.6577, 'end': 924697.6603, 'dur_s': 0.0026, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'first_AMZN_3', 'start': 924697.6661, 'end': 924697.6661, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'first_AMZN_3', 'start': 924697.6661, 'end': 924697.6661, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'first_AMZN_3', 'start': 924697.6671, 'end': 924697.6741, 'dur_s': 0.007, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'first_AMZN_3', 'start': 924697.667, 'end': 924697.6741, 'dur_s': 0.0071, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'first_AMZN_3', 'start': 924637.2638, 'end': 924697.6743, 'dur_s': 60.4105, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'first_AMZN_3', 'start': 924636.9254, 'end': 924697.7074, 'dur_s': 60.782, 'detail': 'AMZN', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_1_attach_QQQ', 'start': 924699.4941, 'end': 924699.4941, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_1_attach_QQQ', 'start': 924699.4941, 'end': 924699.4987, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_1_attach_QQQ', 'start': 924699.4987, 'end': 924699.4993, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'switch_1_attach_QQQ', 'start': 924699.4992841, 'end': 924699.4992842, 'dur_s': 0.0, 'detail': 'call #3 on thread asyncio_3', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_1_attach_QQQ', 'start': 924699.5004, 'end': 924699.7377, 'dur_s': 0.2374, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_1_attach_QQQ', 'start': 924699.5002, 'end': 924699.7378, 'dur_s': 0.2376, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_attach_QQQ', 'start': 924699.738, 'end': 924700.443, 'dur_s': 0.705, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_attach_QQQ', 'start': 924699.7382, 'end': 924700.7369, 'dur_s': 0.9988, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_attach_QQQ', 'start': 924699.7382, 'end': 924753.42, 'dur_s': 53.6818, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'switch_1_attach_QQQ', 'start': 924699.7378, 'end': 924753.5382, 'dur_s': 53.8004, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_1_attach_QQQ', 'start': 924753.5383, 'end': 924753.5383, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_1_attach_QQQ', 'start': 924753.5383, 'end': 924753.5383, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_1_attach_QQQ', 'start': 924753.5385, 'end': 924753.541, 'dur_s': 0.0025, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_1_attach_QQQ', 'start': 924753.5473, 'end': 924753.5554, 'dur_s': 0.0081, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_1_attach_QQQ', 'start': 924753.5472, 'end': 924753.5555, 'dur_s': 0.0082, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_1_attach_QQQ', 'start': 924699.4993, 'end': 924753.5557, 'dur_s': 54.0565, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_1_attach_QQQ', 'start': 924699.2197, 'end': 924753.6652, 'dur_s': 54.4455, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_1_to_AMZN', 'start': 924755.4579, 'end': 924755.4579, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_1_to_AMZN', 'start': 924755.4579, 'end': 924755.4625, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_1_to_AMZN', 'start': 924755.4625, 'end': 924755.463, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'switch_1_to_AMZN', 'start': 924755.4630421, 'end': 924755.4630422, 'dur_s': 0.0, 'detail': 'call #4 on thread asyncio_1', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_1_to_AMZN', 'start': 924755.4639, 'end': 924755.6998, 'dur_s': 0.2359, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_1_to_AMZN', 'start': 924755.4638, 'end': 924755.6999, 'dur_s': 0.2361, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_to_AMZN', 'start': 924755.7002, 'end': 924756.399, 'dur_s': 0.6988, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_to_AMZN', 'start': 924755.7003, 'end': 924757.5845, 'dur_s': 1.8842, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_to_AMZN', 'start': 924755.7003, 'end': 924757.6098, 'dur_s': 1.9094, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_to_AMZN', 'start': 924755.7003, 'end': 924815.6965, 'dur_s': 59.9962, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_1_to_AMZN', 'start': 924755.7004, 'end': 924815.6966, 'dur_s': 59.9963, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'switch_1_to_AMZN', 'start': 924755.6999, 'end': 924815.7086, 'dur_s': 60.0087, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_1_to_AMZN', 'start': 924815.7087, 'end': 924815.7087, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_1_to_AMZN', 'start': 924815.7087, 'end': 924815.7087, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_1_to_AMZN', 'start': 924815.7089, 'end': 924815.7089, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'switch_1_to_AMZN', 'start': 924815.7089, 'end': 924815.7089, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'switch_1_to_AMZN', 'start': 924815.7089, 'end': 924815.7089, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_1_to_AMZN', 'start': 924815.71, 'end': 924815.7187, 'dur_s': 0.0087, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_1_to_AMZN', 'start': 924815.7099, 'end': 924815.7187, 'dur_s': 0.0088, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_1_to_AMZN', 'start': 924755.463, 'end': 924815.7189, 'dur_s': 60.2559, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_1_to_AMZN', 'start': 924755.1699, 'end': 924815.755, 'dur_s': 60.5851, 'detail': 'AMZN', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_2_attach_QQQ', 'start': 924817.578, 'end': 924817.578, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_2_attach_QQQ', 'start': 924817.578, 'end': 924817.5831, 'dur_s': 0.0051, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_2_attach_QQQ', 'start': 924817.5831, 'end': 924817.5836, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_2_attach_QQQ', 'start': 924817.5838, 'end': 924817.8166, 'dur_s': 0.2328, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_2_attach_QQQ', 'start': 924817.5836, 'end': 924817.8167, 'dur_s': 0.2331, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_attach_QQQ', 'start': 924817.817, 'end': 924818.5269, 'dur_s': 0.7099, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_attach_QQQ', 'start': 924817.8171, 'end': 924819.7198, 'dur_s': 1.9027, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_attach_QQQ', 'start': 924817.8172, 'end': 924854.3369, 'dur_s': 36.5197, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'switch_2_attach_QQQ', 'start': 924817.8167, 'end': 924854.4515, 'dur_s': 36.6348, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_2_attach_QQQ', 'start': 924854.4515, 'end': 924854.4515, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_2_attach_QQQ', 'start': 924854.4516, 'end': 924854.4516, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_2_attach_QQQ', 'start': 924854.4518, 'end': 924854.455, 'dur_s': 0.0032, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_2_attach_QQQ', 'start': 924854.4619, 'end': 924854.469, 'dur_s': 0.0071, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_2_attach_QQQ', 'start': 924854.4618, 'end': 924854.469, 'dur_s': 0.0072, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_2_attach_QQQ', 'start': 924817.5836, 'end': 924854.4693, 'dur_s': 36.8857, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_2_attach_QQQ', 'start': 924817.2731, 'end': 924854.5076, 'dur_s': 37.2345, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_2_to_AMZN', 'start': 924856.3323, 'end': 924856.3323, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_2_to_AMZN', 'start': 924856.3323, 'end': 924856.3373, 'dur_s': 0.0049, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_2_to_AMZN', 'start': 924856.3373, 'end': 924856.3379, 'dur_s': 0.0006, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'switch_2_to_AMZN', 'start': 924856.3379253, 'end': 924856.3379254, 'dur_s': 0.0, 'detail': 'call #5 on thread asyncio_2', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_2_to_AMZN', 'start': 924856.3389, 'end': 924856.5817, 'dur_s': 0.2429, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_2_to_AMZN', 'start': 924856.3387, 'end': 924856.5818, 'dur_s': 0.2431, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924856.5821, 'end': 924857.2911, 'dur_s': 0.709, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924856.5823, 'end': 924857.7683, 'dur_s': 1.186, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924856.5823, 'end': 924858.9259, 'dur_s': 2.3436, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924856.5823, 'end': 924916.5927, 'dur_s': 60.0105, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': 'CancelledError: '}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924856.5823, 'end': 924916.5928, 'dur_s': 60.0104, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': 'CancelledError: '}
{'segment': 'warm_total', 'run': 'switch_2_to_AMZN', 'start': 924856.5818, 'end': 924916.5928, 'dur_s': 60.011, 'detail': '', 'exc': 'TimeoutError: no answer in 60s (request_timeout_s)'}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924916.5936, 'end': 924917.3004, 'dur_s': 0.7068, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_2_to_AMZN', 'start': 924916.5929, 'end': 924917.301, 'dur_s': 0.7081, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_2_to_AMZN', 'start': 924916.5929, 'end': 924917.301, 'dur_s': 0.7082, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924917.3013, 'end': 924918.0172, 'dur_s': 0.7159, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_2_to_AMZN', 'start': 924917.3011, 'end': 924918.0227, 'dur_s': 0.7216, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_2_to_AMZN', 'start': 924917.3011, 'end': 924918.0227, 'dur_s': 0.7216, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924918.0231, 'end': 924962.0679, 'dur_s': 44.0448, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_2_to_AMZN', 'start': 924918.0229, 'end': 924962.1754, 'dur_s': 44.1525, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_2_to_AMZN', 'start': 924918.0229, 'end': 924962.1784, 'dur_s': 44.1555, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924962.1841, 'end': 924998.5549, 'dur_s': 36.3709, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_2_to_AMZN', 'start': 924962.1838, 'end': 924998.6371, 'dur_s': 36.4533, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_2_to_AMZN', 'start': 924962.1838, 'end': 924998.6389, 'dur_s': 36.4551, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'switch_2_to_AMZN', 'start': 924962.1838, 'end': 924998.6389, 'dur_s': 36.4552, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_2_to_AMZN', 'start': 924998.6392, 'end': 924999.3599, 'dur_s': 0.7206, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_2_to_AMZN', 'start': 924998.639, 'end': 924999.3638, 'dur_s': 0.7248, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_2_to_AMZN', 'start': 924998.639, 'end': 924999.3638, 'dur_s': 0.7248, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'switch_2_to_AMZN', 'start': 924998.639, 'end': 924999.3638, 'dur_s': 0.7248, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_2_to_AMZN', 'start': 924999.374, 'end': 924999.3808, 'dur_s': 0.0068, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_2_to_AMZN', 'start': 924999.3739, 'end': 924999.3808, 'dur_s': 0.0069, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_2_to_AMZN', 'start': 924856.3379, 'end': 924999.3811, 'dur_s': 143.0432, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_2_to_AMZN', 'start': 924856.0284, 'end': 924999.4724, 'dur_s': 143.444, 'detail': 'AMZN', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_3_attach_QQQ', 'start': 925001.2491, 'end': 925001.2491, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_3_attach_QQQ', 'start': 925001.2491, 'end': 925001.2538, 'dur_s': 0.0047, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_3_attach_QQQ', 'start': 925001.2538, 'end': 925001.2544, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'switch_3_attach_QQQ', 'start': 925001.2543735, 'end': 925001.2543735, 'dur_s': 0.0, 'detail': 'call #6 on thread asyncio_4', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_3_attach_QQQ', 'start': 925001.2553, 'end': 925001.4914, 'dur_s': 0.2361, 'detail': 'QQQ', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_3_attach_QQQ', 'start': 925001.2552, 'end': 925001.4915, 'dur_s': 0.2364, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_attach_QQQ', 'start': 925001.4918, 'end': 925002.1963, 'dur_s': 0.7045, 'detail': 'QQQ dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_attach_QQQ', 'start': 925001.4919, 'end': 925003.631, 'dur_s': 2.1391, 'detail': 'QQQ dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_attach_QQQ', 'start': 925001.492, 'end': 925053.5532, 'dur_s': 52.0612, 'detail': 'QQQ dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'switch_3_attach_QQQ', 'start': 925001.4916, 'end': 925053.6683, 'dur_s': 52.1767, 'detail': '', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_3_attach_QQQ', 'start': 925053.6683, 'end': 925053.6683, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_3_attach_QQQ', 'start': 925053.6684, 'end': 925053.6684, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_3_attach_QQQ', 'start': 925053.6686, 'end': 925053.6712, 'dur_s': 0.0026, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_3_attach_QQQ', 'start': 925053.6781, 'end': 925053.686, 'dur_s': 0.0079, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_3_attach_QQQ', 'start': 925053.678, 'end': 925053.686, 'dur_s': 0.0079, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_3_attach_QQQ', 'start': 925001.2544, 'end': 925053.6862, 'dur_s': 52.4319, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_3_attach_QQQ', 'start': 925000.9929, 'end': 925053.7253, 'dur_s': 52.7324, 'detail': 'QQQ', 'exc': ''}
{'segment': '1_begin_attach', 'run': 'switch_3_to_AMZN', 'start': 925055.6369, 'end': 925055.6369, 'dur_s': 0.0, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_3_to_AMZN', 'start': 925055.6369, 'end': 925055.6415, 'dur_s': 0.0046, 'detail': '', 'exc': ''}
{'segment': '3_worker_dispatch_gap', 'run': 'switch_3_to_AMZN', 'start': 925055.6415, 'end': 925055.6421, 'dur_s': 0.0005, 'detail': '', 'exc': ''}
{'segment': 'EVENT_LOOP_CREATED', 'run': 'switch_3_to_AMZN', 'start': 925055.6420686, 'end': 925055.6420687, 'dur_s': 0.0, 'detail': 'call #7 on thread asyncio_5', 'exc': ''}
{'segment': 'WIRE_reqContractDetails', 'run': 'switch_3_to_AMZN', 'start': 925055.643, 'end': 925055.8803, 'dur_s': 0.2373, 'detail': 'AMZN', 'exc': ''}
{'segment': 'resolve', 'run': 'switch_3_to_AMZN', 'start': 925055.6428, 'end': 925055.8804, 'dur_s': 0.2376, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925055.8807, 'end': 925056.5818, 'dur_s': 0.7012, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925055.8808, 'end': 925057.569, 'dur_s': 1.6882, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925055.8809, 'end': 925057.5894, 'dur_s': 1.7085, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'warm_total', 'run': 'switch_3_to_AMZN', 'start': 925055.8804, 'end': 925115.8915, 'dur_s': 60.0111, 'detail': '', 'exc': 'TimeoutError: no answer in 60s (request_timeout_s)'}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925055.8809, 'end': 925115.8919, 'dur_s': 60.0111, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925055.881, 'end': 925115.8921, 'dur_s': 60.0111, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925115.8922, 'end': 925116.8134, 'dur_s': 0.9212, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_3_to_AMZN', 'start': 925115.8916, 'end': 925116.8139, 'dur_s': 0.9223, 'detail': 'AMZN dur=1 Y size=1 day rth=True', 'exc': ''}
{'segment': 'role_daily_bars', 'run': 'switch_3_to_AMZN', 'start': 925115.8916, 'end': 925116.8139, 'dur_s': 0.9224, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925116.8142, 'end': 925117.5592, 'dur_s': 0.745, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_3_to_AMZN', 'start': 925116.814, 'end': 925117.5647, 'dur_s': 0.7507, 'detail': 'AMZN dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_3_to_AMZN', 'start': 925116.814, 'end': 925117.5647, 'dur_s': 0.7507, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925117.5651, 'end': 925153.3604, 'dur_s': 35.7952, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_3_to_AMZN', 'start': 925117.5648, 'end': 925153.4687, 'dur_s': 35.9039, 'detail': 'AMZN dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_3_to_AMZN', 'start': 925117.5648, 'end': 925153.4716, 'dur_s': 35.9068, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925153.4776, 'end': 925184.4429, 'dur_s': 30.9653, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_3_to_AMZN', 'start': 925153.4773, 'end': 925184.5902, 'dur_s': 31.1128, 'detail': 'XLC dur=20 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_intraday_sessions', 'run': 'switch_3_to_AMZN', 'start': 925153.4773, 'end': 925184.5922, 'dur_s': 31.1149, 'detail': '', 'exc': ''}
{'segment': 'role_sector_sessions', 'run': 'switch_3_to_AMZN', 'start': 925153.4773, 'end': 925184.5922, 'dur_s': 31.1149, 'detail': '', 'exc': ''}
{'segment': 'WIRE_reqHistoricalData', 'run': 'switch_3_to_AMZN', 'start': 925184.5928, 'end': 925185.7413, 'dur_s': 1.1485, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'FALLBACK_bars', 'run': 'switch_3_to_AMZN', 'start': 925184.5923, 'end': 925185.746, 'dur_s': 1.1538, 'detail': 'XLC dur=1 D size=1 min rth=False', 'exc': ''}
{'segment': 'role_today_minutes', 'run': 'switch_3_to_AMZN', 'start': 925184.5923, 'end': 925185.7461, 'dur_s': 1.1538, 'detail': '', 'exc': ''}
{'segment': 'role_sector_today_minutes', 'run': 'switch_3_to_AMZN', 'start': 925184.5922, 'end': 925185.7461, 'dur_s': 1.1538, 'detail': '', 'exc': ''}
{'segment': '2_rerender_after_begin', 'run': 'switch_3_to_AMZN', 'start': 925185.756, 'end': 925185.7637, 'dur_s': 0.0077, 'detail': '', 'exc': ''}
{'segment': '5_finish_attach_incl_rerender', 'run': 'switch_3_to_AMZN', 'start': 925185.7559, 'end': 925185.7637, 'dur_s': 0.0078, 'detail': '', 'exc': ''}
{'segment': '4_attach_worker_total', 'run': 'switch_3_to_AMZN', 'start': 925055.6421, 'end': 925185.764, 'dur_s': 130.1219, 'detail': '', 'exc': ''}
{'segment': '0_TOTAL_keypress_to_paint', 'run': 'switch_3_to_AMZN', 'start': 925055.2391, 'end': 925185.8021, 'dur_s': 130.563, 'detail': 'AMZN', 'exc': ''}
```

---

## Closing sequence

`verify.ps1`/`export-handoff.ps1`/commit/push follow this note, from the
main checkout, scoped to this task's own files (this done-note and the
`075` inbox file). No production source file was touched by this task, so
`verify.ps1`'s suite result is expected unchanged from `072`'s close.

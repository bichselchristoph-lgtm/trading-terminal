---
recorded: 2026-08-07
status: OBSERVATION_UNVALIDATED
review_trigger: live_gains_test_coverage
review_trigger_kind: gate
priority: FIRST_BEHAVIOURAL_TEST
review_trigger_note: >
  Cannot be acted on safely until live/ has behavioural tests. Today it has an
  import smoke test only, so changing which Session it uses would be an
  unverifiable change to the operational path.

  SCHEDULED 2026-08-07 as the FIRST behavioural test to write, ahead of any
  other live/ coverage. Two reasons: it is a known-wrong calculation rather
  than an untested one, and live/ behavioural coverage is now a precondition
  for merging tws_order -- so the first test written is also the first step
  toward putting order-placing code under verification. A known-wrong
  calculation on a path that will eventually size positions is the right place
  to start.
---

# OBSERVATION — Session is defined twice, and the live one is calendar-blind

Found while resolving `live/_to_merge/` for consolidation step 7.

## The two definitions

| | `core/session.py` | `live/marketstate.py` (was `tradesignals/core.py`) |
|---|---|---|
| concept | `SessionHours`, `SessionBounds`, `Phase`, `SessionCalendar` | `Session` |
| boundaries | from a maintained holiday/half-day table, 2019–2027 | from config strings, `09:30`/`16:00` |
| holidays | known; raises outside coverage | **unknown** |
| half days | known; `rth_fraction` for comparability | **treated as full days** |
| opening range | not modelled | `breakout_minutes`, `or_end_ns` |

Both map timestamps onto pre-market / RTH / post-market. `core`'s is strictly
richer except for the opening range, which only `live` has.

## Why this is worth recording rather than fixing now

The live `Session` computes `rth_close` from a config string, so on a half day
it places the close at 16:00 when the market shut at 13:00. Every downstream
quantity anchored to the close — the closing bar, session VWAP, any
close-relative measure — is then computed over a window that includes three
hours of nothing.

That is the same class as the tz-conversion bug that shifted every daily bar by
a day: not a crash, a well-formed number over the wrong window.

## Why it is not fixed here

`live/` has no behavioural tests — only the import smoke test added alongside
this note. Swapping its session model is a change to the operational path that
nothing would verify. It also needs a decision the code cannot make: the
opening-range concept (`breakout_minutes`, `or_end_ns`) exists only on the live
side, so a merge is not a deletion but a question about where opening-range
structure belongs.

## What would decide it

Run the live console against a known half day — 2024-11-29 or 2025-12-24, both
in the calendar table and both already used as fixtures in
`tests/test_us_equity_calendar.py` — and check whether the session boundary it
reports matches the calendar's. Needs a replay slice, no live connection, no
spend.

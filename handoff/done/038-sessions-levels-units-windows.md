---
id: 038
title: Sessions, levels, units and windows — amended in SPEC and enforced in code
type: spec
class: admin
owner: claude-code
supersedes: 035, 035a, 036
depends: 034, 037
---

**Status** RUNNING

# 038 — done. The basis is a constant, and every rendered number carries it.

**`ATR14` was computed on regular-session daily bars and read `13.14` against Christoph's TWS
daily ATR(14) of ≈`15.6` — −16 %.** It went straight into the 3×ATR stop floor and therefore
into every share count, as a well-formed number with nothing on the screen to question.

**The cause was one request.** `live/attach/ibkr.py:daily_bars` issued a single
`reqHistoricalData(..., useRTH=True)` and that one series fed ADR%, ADR $, the 10/20/50 SMA
stack, `PDH`/`PDL` **and** `ATR14`. The module's docstring explained at length why `useRTH` must
be declared at every call site. It was declared, at every call site, and it was wrong for one of
the five consumers — **which is the shape of this defect: the comment was right and the flag was
not.**

---

## 0 — before anything else, three corrections to the task file

**`038` §"How to amend" asked for exactly this**: *if any instruction contradicts what is
actually in `SPEC.md`, report the contradiction and stop on that part rather than overwriting.*

**1. `SPEC.md:999` was not the only place the wrong claim lived.** `038` names it, and §4.4's
`use_rth` table carried the same assertion independently, with its own justification: *"on
TradingView the extended-hours toggle is labelled 'Extended Hours (Intraday only)' — it provably
cannot affect a daily bar. TC2000 … is the same."* **Both are facts about charting platforms and
neither is a fact about IBKR's historical endpoint.** Both are corrected. Fixing only the line
`038` named would have left the reasoning intact one section away.

**2. `038` Part 1 does not rule on the SMA stack or on 52wH/52wL.** Its table names PDC, PDO,
PDH/PDL, PMH/PML, AMH/AML, ORH/ORL, and its statistic distinction covers ADR and ATR. **The SMA
stack is neither.** `036` proposed ETH for it and `036` is superseded, so **it keeps the RTH
basis it already had and nothing was changed on inference.** Declared as `SMA_BASIS` and
`YEAR_BASIS` with `why: UNRULED by 038` so the gap is visible in code. `OBS-051` holds it open.
**This needs a ruling and it is a real question, not a formality** — see §6.

**3. §4.0a and `038` Part 2 disagree on one character.** §4.0a's example renders a percentage as
`2.8 %` with a space; `038` renders `78%` without. The implementation follows `038`, and the
difference is recorded in `SPEC.md` §4.4a.4 rather than silently resolved.

---

## 1 — the pre-fix `use_rth` table, before anything was changed

**This is the finding, and it is the state as found, not as fixed.** One row per daily-bar
request in `live/attach/ibkr.py` at commit `f2b05c2`.

| fetch | request | `use_rth` as found | consumers |
|---|---|---|---|
| `daily_bars` | `60 D` · `1 day` | **`True`** — literal at the call site | **ADR%, ADR $, ADR used, room up, room down, ext 10/20/50, ATR14, PDH, PDL** |
| `intraday_sessions` | `20 D` · `1 min` | `False` — literal | the 20-session RVOL curve |
| `today_minutes` | `1 D` · `1 min` | `False` — literal | VWAP, cum vol, PMH/PML, ORH/ORL |
| `year_high_low` | `1 Y` · `1 day` | **`True`** — literal | 52wH, 52wL |

**Ten rendered values came off one flag.** Four of the five call sites passed a boolean literal;
the fifth passed one too. Nothing was configurable and nothing was named.

**Nothing else in the tree requests bars.** `038` asked me to look, so: `grep` for
`reqHistoricalData` / `reqHistoricalTicks` across the tracked tree finds them only in
`live/attach/ibkr.py` and in `tools/probe_keepuptodate_scale.py`, which is a one-off probe
under `021` and not part of the terminal. **`tests/test_session_basis.py` now parses
`ibkr.py` with `ast` and fails on any `use_rth=` / `useRTH=` literal**, so a new call site
cannot reintroduce one.

---

## 2 — before and after, with bases

| Row | Before | After | Basis, as it now renders |
|---|---|---|---|
| **ATR14** | `13.14` | **ETH-derived** | `04:00-20:00 ET` |
| **PDL** | RTH low, unlabelled | **RTH low, labelled** | `09:30-16:00 ET` |
| **PDH** | `727.25` | `$727.25` | `09:30-16:00 ET` |
| ADR% | `1.63` | `1.6%` | `09:30-16:00 ET` |
| ADR $ | `11.83` | `$11.83` | `09:30-16:00 ET` |
| ADR used | `67.00` | `67.0% of $11.83 · from today's open` | `09:30-16:00 ET` |
| room up / down | `3.90` / `19.76` | `$3.90` / `$19.76` | `09:30-16:00 ET` |
| ext 10/20/50 | `1.39` | `1.4 ADR` | `09:30-16:00 ET` |
| VWAP | `730.84` | `$730.84` | `04:00 anchor · 04:00-20:00 ET` |
| cum vol | `18,119,366.00` | `18.1M sh` | `04:00 anchor · 04:00-20:00 ET` |
| RVOL | `0.86` | `0.9× · vs 20d median at 14:39h ET` | `04:00-20:00 ET` |
| PMH / PML | unlabelled | `$725.46` / `$722.80` | `04:00-09:30 ET, today` |
| ORH / ORL | unlabelled | `$726.02` / `$724.03` | `09:30-09:35 ET, today` |
| **round** | **`47.00`** | **`47 levels`** | *(exempt — see §6.2)* |

**`PDL` did not change value in this task** and that is worth stating plainly, because `036`
would have changed it to `717.37` and been wrong. It changed *basis declaration* and *label*.

---

## 3 — the four reds, quoted

Each was produced by mutating the fixed code and running the test. **Verbatim.**

**Test 1 — the constant and the wire disagree.** Mutation: `daily_bars` ignores its `basis`
argument and passes `use_rth=True`, which is the pre-038 code exactly.

```
AssertionError: 04:00-20:00 ET declares use_rth=False and the request issued useRTH=True.
**The constant and the wire disagree**, which is the entire defect 038 exists to close — every
comment in the module can say the right thing while the flag does not.
FAILED tests/test_session_basis.py::test_a_daily_request_carries_the_basis_it_was_asked_with[ATR_BASIS]
FAILED tests/test_session_basis.py::test_no_call_site_passes_a_use_rth_literal
2 failed, 7 passed
```

**Note which parameterisation went red: `[ATR_BASIS]` alone.** The other three declare
`use_rth=True` and a hardcoded `True` satisfies them. **That is precisely why test 2 exists.**

**Test 2 — ADR and ATR configured alike.** Mutation: `ADR_BASIS.use_rth = False`.

```
AssertionError: ADR and ATR both request use_rth=False. **They measure different things over
different sessions on purpose** — ADR has no gap term, ATR is nothing but the gap term. Two
volatility rows four apart on one panel, computed alike, is the reading this task exists to
make impossible.
FAILED tests/test_session_basis.py::test_adr_and_atr_must_not_request_the_same_flag
1 failed, 8 passed
```

**Test 3 — a rendered row loses its basis.** Mutation: `atr_d14` returns `basis=None`.

```
AssertionError: these rows render a number and do not say which session it was computed over:
    ATR14     — (no basis declared)
assert not ['ATR14     — (no basis declared)']
```

**The row refused rather than rendering `15.61` unlabelled**, which is `038`'s exit test holding.

**Test 4 — a unit is removed.** Mutation: the `percent` entry in `config/formatting.yaml` loses
its `suffix`.

```
AssertionError: these rows render a bare number with no unit:
    ADR%: 2.0
    ADR used: 24.9
**All numbers need units** (038 Part 2). Expected one of: '$', '%', ' ADR', '×', ' sh', ' levels'
```

### The mutation caught a defect in the test rather than in the code, and it is worth reading

**On the first run of mutation 4, test 4 stayed GREEN.** The test compared the whole rendered
line against a list of unit marks — and the row's own *label* is `ADR%`, which contains a `%`.
**So stripping the `%` off the percent unit left the number bare and the test satisfied by the
column heading printed beside it.**

That is the self-reference trap `038` Part 5 warns about, in the test written to obey the
warning. It is fixed by asserting against `format_value(m)` — the rendered value alone — and
**the only reason it was found is that `038` asks for each test to be seen red.** A test written
and never failed would have shipped agreeing with itself.

---

## 4 — Part 6's three rows

**1. The ADR trio's anchor is TODAY'S OPEN, and it is identifiable.** Not the prior close.
`adr_dollar` takes `todays_open`; `adr_used` computes `abs(current − todays_open) / ADR$`; and
`room_left` returns `todays_open ± ADR$ − current`. Christoph's screenshot showed `ADR used
67.00` on `ADR $ 11.83`, so `|current − open| = 7.93`; with price at `733.14` that puts the open
at `725.21` **or** `741.07`. The `725.21` that `038` observes *"is neither the extended-hours low
(722.80) nor the opening-range low (724.03)"* is correct — **it is neither, because it is not a
low at all. It is the open.** The rows now say so: they render `· from today's open`.

**2. `round` computes a COUNT, and the label does not match.** `level_rail` returns
`float(len(round_numbers(price, span)))` — **how many half-dollar levels fall within ±ADR$ of
price**, not a level. Confirmed by arithmetic: span `11.83` around `733.14` gives `721.31` to
`744.97`; `round_numbers` steps by `0.50` from `721.50` to `744.50`, which is **exactly 47**.
`47.00` was correct and unreadable.

**Fixed by making the unit honest, not by renaming the row** — `038` puts panel layout out of
scope. It now renders `47 levels · half-dollar levels within ±$11.83 of $733.14`, which cannot
be misread as a price. **Whether the row should exist at all, and under what name, is a
decision I did not make.**

**3. Two decimals on non-monetary values — fixed, and the cause was bigger than the two rows.**
`live/tui/app.py:measured_cell` formatted **every** context value as `f"{m.value:,.2f}"`. There
was no formatter; §4.0a has required *"one function, and its precision comes from config"* since
it was written. So this also produced `18,119,366.00` for a share count where §4.0a asks for
`18.1M sh`. Now `live/tui/numbers.py` + `config/formatting.yaml`.

---

## 5 — RVOL's anchor consistency: verified, and one thing is wrong

**The anchor is consistent. All 20 sessions come from a single `intraday_sessions` request with
a single flag**, split into sessions on the bar's own ET date, and `034`'s `_eastern()`
normalisation happens at the seam *before* the split. There is no path by which two sessions in
the lookback carry different anchors — that would need two requests, and there is one.

**But the label can overstate the sample.** `rvol_curve` appends a session's cumulative volume
to a minute key **only if that session has a bar at that minute**, so on a lookback containing a
half day the median at 15:30 is over 19 sessions. `rvol_at` renders `vs {sessions_used}d median`
where `sessions_used` is the constant `RVOL_SESSIONS = 20`, **not the length of the list actually
median-ed.** The ratio is right; the row's claim about what it was measured against is not, at
exactly the minutes where the reference thins.

**Not fixed here** — `038` rules on bases and units, and changing what a sample string counts is
a separate decision. `OBS-048`, and it is filed as a **READING**: it comes from reading the code,
no half day sits in any fixture, and it has not been observed on real bars.

---

## 6 — what I could not do, and what I did not do

**1. `PDL` has no externally-checked value and therefore is not pinned as one.** The UAT supplied
the *extended-hours* low, `717.37`. Under Part 1 that figure is `AML`. **The regular-session
prior-day low was never supplied by any chart in `013`**, so `test_qqq_2026_08_13_regression.py`
pins the **property** — `PDL` reads the RTH series and is not `717.37` — and uses `723.55` as an
explicitly-labelled *fixture constant, not a check*. **Christoph can close this in one minute
from the TWS regular-session chart for 8/12, and until he does, five of the six pinned levels are
externally verified and the sixth is not.**

**2. `ADR%` and `ADR $` are deliberately absent from the fixture, and this is not an oversight.**
TWS has no native ADR; any figure it shows comes from a different computation over a different
bar set. Recording it would be a check that never happened. There is a test whose whole body says
so, `test_adr_percent_is_not_pinned_against_tws`.

**3. The SMA stack and 52wH/52wL are unruled and untouched** — §0.2 above, `OBS-051`.

**4. Parts 3 and 4 are specified and not built**, as `038` requires: the level-state vocabulary,
`clear for`, and the two tape windows are in `SPEC.md` §4.4a.5–6. **`room up` / `room down` are
still rendered**, because `clear for` replaces them and building it is a panel change `038` puts
out of scope.

**5. The four-decimal sub-dollar price rule is implemented but never exercised on real data.**
§4.0a asks for 4 decimals below $1.00; there is a unit test and no sub-dollar instrument has been
attached.

**6. I did not run the terminal.** Everything here is fixtures and tests. The values Christoph
sees depend on IBKR returning what `SPEC.md` now says it returns, and **the only evidence that it
does is his own chart comparison, not a measurement made from this tree.** `c018` is the check.

---

## 7 — the tests

**12 failed, 369 passed.** The baseline at `f2b05c2` in the same worktree was **12 failed, 342
passed** — so **27 tests added, no regression, and the 12 failures are pre-existing and
untouched.** They are: `test_evidence_carry_intact` (2), `test_export_scope_is_derived`,
`test_handoff_state_declared`, `test_observations_ledger` (2, the UAT register missing rows for
`013`/`014`/`015`), `test_regime_prompt_invariants` (2), `test_regime_snapshot_could_not_do`,
`test_spec_pointers`, `test_sync_from_drive`, `test_uat_has_a_file`.

**`037`'s done-note recorded 8 failed / 346 passed. Four more were already red before I touched
anything**, and I did not diagnose them — they are outside `038` and several read state outside
the repo. **Flagging the drift rather than absorbing it.**

**The adoption gate fired on commit**, on all four new files plus the amended core module, and it
was right to: a file that arrives by any route other than adoption or evidence carry goes red,
including one this session wrote itself. Six rows added to `ADOPTION-LOG.md`.

---

## 8 — what landed

| file | what |
|---|---|
| `core/indicators/context.py` | `SessionBasis`, six basis constants, `Unit`, and `unit`/`basis` on every `Measured` |
| `live/attach/ibkr.py` | `daily_bars(c, basis)` — the flag comes from the constant, never a literal |
| `live/attach/attach.py` | dailies requested **once per distinct basis**, memoised on the flag |
| `live/tui/numbers.py` | **new** — §4.0a's one formatter, and the no-basis refusal |
| `config/formatting.yaml` | **new** — §4.0a's precisions, as config |
| `docs/specs/SPEC.md` | §4.4a added (six windows, basis-in-code, bases rendered, units, level state, tape windows); §4.4 and §6b.1b-ATR corrected in place, **struck rather than deleted** |
| `docs/observations/OBSERVATIONS.md` | `OBS-047` … `OBS-052`, one `PROMOTED` with its resolution |
| three new test files | 27 tests |

**Memoised on the flag, not on the indicator** — two indicators sharing a basis share the
request, because IBKR's pacing budget is ~60 historical requests per 10 minutes and one request
per indicator would spend it. Each indicator still *asks* with its own constant, so flipping one
basis moves that indicator alone.

---

## 9 — for Christoph

**`c018` is the check that matters**: attach QQQ and compare `ATR14` against the TWS **ETH**
daily chart — it must agree — and `PDL` against the **regular-session** low for the prior day,
which the ETH chart will not show directly.

**And one thing only you can answer**: the prior regular-session low for QQQ on 2026-08-12. It
turns the sixth fixture pin from a fixture constant into an externally-checked value.

---

**This note needs to be pasted to chat.** It lands in a repo the design session cannot see, and
on 2026-08-11 two correct done-notes never reached it. **Writing it is not reporting it.**

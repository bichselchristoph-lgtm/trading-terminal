---
id: 001
title: Register rvol_vs_trailing in the indicator registry
status: READY
depends_on: []
touches_phase3: false
---

# TASK 001 — Register `rvol_vs_trailing` (conformance, not a build)

## What changed since this task was first written

The original artifact said "build a historical-average RVOL indicator from
scratch." That was wrong, and the correction matters:

- `orb_tools/volume_curve.py` already has `relative_volume(cum_volume,
  avg_daily_volume, now_et, curve)` — projected full-day volume over ADV.
- `reference.rvol_session_at(cum_vol_today, cum_vol_curve_at_t)` is the SAME
  measure algebraically: projecting with the curve and dividing by ADV is
  dividing by expected-cumulative-at-t. `cum / (frac x ADV)` either way.

So the curve-based measure exists and is already named `rvol_vs_curve`.

What does NOT exist is the EMPIRICAL PER-NAME baseline. That is this task.

## The distinction being registered

The axis is BASELINE PROVENANCE, not direction:

| entry | baseline | status |
|---|---|---|
| `rvol_vs_curve` | ADV x a generic shape prior | exists; prior untested on this population (registered v21) |
| `rvol_vs_trailing` | that name's OWN trailing N sessions, same clock window | THIS TASK |
| `deepvue_rvol` | unknown, arrives from the CSV | renamed at the ingestion boundary, never mixed |

Both are legitimate. Neither supersedes the other. They answer different
questions, and an `Rvol` already carries its basis with `comparable_to()`
refusing across bases — `rvol_vs_trailing` must participate in that.

## Contract

    rvol_vs_trailing(bars, asof, window_minutes) -> Rvol | None

- `bars`: the window the harness supplies per the `lookback` field — NOT a
  frame the indicator fetches for itself.
- `asof`: the cutoff, pinned to CONFIRMATION (Amdt 3). Data `<= asof` ONLY.
- `window_minutes`: trailing measurement window ending at `asof`. Multi-window
  is the SAME function called with 1 / 5 / 15 / 60 — not four functions.
- Returns today's volume in that window divided by the mean of the SAME clock
  window across the prior sessions in `bars`. Carries basis `TRAILING`.

## Registry conformance — the actual work

1. `@signal` decorator + `SignalSpec`, so `REGISTRY` knows about it.
2. `lookback` is REQUIRED with no default. `rvol_vs_trailing` declares 10.
   (The ten existing indicators declare 1; design rule 1 is the degenerate
   case of the wider rule, not an exception to it.)
3. `scored = False`. Registering an indicator must NOT enlarge the
   pre-registered scored set from ten. `REGISTRY.scored()` stays at ten and
   the test pinning that must still pass.
4. The measurement window is a PARAMETER, never a module constant (Amdt 5a).
5. Returns a raw ratio wrapped in `Rvol` — no scoring, no verdict, no fit
   status. Composition adds those later (Amdt 7, Tenet 3).

## Rules it must honour

- `None`, never 0, when there is no baseline. Absence != zero (Tenet 2).
- INSUFFICIENT HISTORY RAISES. `prepare_window()` already does this and the
  existing message is the right one: a ratio over 3 sessions when 10 were
  declared is a well-formed number answering a DIFFERENT question. Do NOT
  compute over what exists.
- EFFECTIVE COUNT. Ten sessions available with three empty after the cutoff
  currently passes `prepare_window` and then averages over seven, silently.
  The returned `Rvol` must carry how many sessions actually contributed, so
  "7 of 10 declared" is a visible property and a per-playbook threshold rather
  than a hidden one. This is the same class as `midday_vol_ratio` reading
  effective count 8 — discovered after the fact in section 6.
- Cutoff-safe: window is `(asof - window, asof]`. A bar after `asof` must not
  change the result.
- Pure and deterministic. No I/O, no clock reads, no side effects.

## Tests

- 1-min window over a 5x first-minute burst -> ~5.0; 5 / 15 / 60-min windows
  dilute it -> ~3.0. (Verified against a synthetic 11-session series.)
- No baseline -> None. `asof` before the open -> None. Zero baseline -> None.
- Insufficient history -> RAISES, and the exception carries declared and
  available.
- Ten sessions with three empty post-cutoff -> ratio whose effective count
  reads 7, not 10.
- Look-ahead guard: appending a bar after `asof` does not change the result.
- `comparable_to()` refuses between an `Rvol` with basis TRAILING and one with
  basis CURVE.
- `REGISTRY.scored()` still returns exactly ten after this registration.

## Reference implementation (verified to run)

    def _window_vol(day_df, win_start_t, asof_t):
        t = day_df.index.time
        mask = (t > win_start_t) & (t <= asof_t)
        return day_df.loc[mask, "volume"].sum() if mask.any() else np.nan

    def rvol_vs_trailing(bars, asof, window_minutes, lookback_sessions=10):
        asof = pd.Timestamp(asof)
        df = bars.loc[bars.index <= asof]
        if df.empty:
            return None
        win_start_t = (asof - pd.Timedelta(minutes=window_minutes)).time()
        asof_t = asof.time()
        today = asof.date()
        today_vol = _window_vol(df[df.index.date == today], win_start_t, asof_t)
        prior_days = sorted({d for d in df.index.date if d < today})[-lookback_sessions:]
        if not prior_days:
            return None
        prior = [_window_vol(df[df.index.date == d], win_start_t, asof_t) for d in prior_days]
        contributing = [v for v in prior if v == v and v > 0]
        if not contributing:
            return None
        baseline = float(np.mean(contributing))
        if baseline == 0:
            return None
        return Rvol(value=float(today_vol) / baseline,
                    basis=RvolBasis.TRAILING,
                    effective_count=len(contributing),
                    declared_count=lookback_sessions)

Note: matches the intraday slice on clock time. If session length or DST can
vary for the instrument, match on minutes-since-open instead of wall-clock
`.time()`.

## Explicitly NOT in this task

- Cross-sectional RVOL and peer-normalized RVOL. Both need sector peer-set
  classification, which is an open data gap.
- Any scoring, fit status, or predicted-direction calibration — phase 3.
- Choosing the per-playbook default DISPLAY window. Compute all four, decide
  the default separately, and pre-register only the window(s) actually being
  calibrated rather than all twelve combinations.

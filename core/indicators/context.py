"""The context block's arithmetic — S010 part 3, `SPEC.md` §6b.1a and §8.4.

**Pure. Nothing here fetches, caches, writes, or knows what a terminal is.**
Bars in, `Measured` out. That is what lets S010's whole surface be tested today
against fixtures while the `019` capture holds the only TWS connection.

**`core` imports nothing first-party**, so this module cannot reach `live.tui`'s
grammar. It returns its own `Measured` and `live/attach/render.py` bridges it to
a `Cell` — the same shape S009 used for `Result`, and the reason is the same: a
core that knows about the screen is a core that cannot be reused off it.

----

**Every value carries what it was computed over.** S010 part 2: *no settle
timer — render the sample instead*, because *n* seconds is the wrong unit. 30 s
is thousands of prints on a liquid name and four on a thin one at 11:40. So
`Measured.sample` is not decoration; it is the field that answers *should I
trust this*, per symbol, which a fixed timer cannot.

**There is no third state.** A daily-derived value is fetched or it is
`unavailable (reason)`. `warming` survives on tape baselines alone and there are
no tape components in core, so nothing here warms — and nothing here may invent
a half-populated state, because there is no cache that could produce one.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

#: `SPEC.md` §6b.1a — Kullamägi's convention. **20, not 14.** TradingView's
#: built-in ADR and its screener ADR% both use 14 and a different estimator;
#: crossing the two produces disagreement before session definitions are even in
#: play. Named and versioned rather than inline, per the threshold convention.
ADR_DEFAULT_N = 20

#: Wilder's period. `atr_d14` is what the 3×ATR stop floor consumes.
ATR_DEFAULT_N = 14

#: §8.4 — the RVOL denominator is a curve over the last N sessions.
RVOL_SESSIONS = 20


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar. `wap` is IBKR's own weighted average for the bar.

    `wap` is optional because daily bars do not need it; **VWAP refuses rather
    than substituting `close` when it is absent**, since a VWAP computed off
    closes is a different quantity wearing the same label.
    """

    ts: str                      # ISO timestamp, or "YYYY-MM-DD" for dailies
    open: float
    high: float
    low: float
    close: float
    volume: float
    wap: Optional[float] = None


@dataclass(frozen=True)
class Measured:
    """A number, **or a named reason there is none.** Never both, never neither.

    `sample` is what it was computed over — `20 sessions`, `18.4M sh · 42 min ·
    from 09:30:00`. S010 requires it on every rendered value.
    """

    value: Optional[float]
    sample: str = ""
    unavailable: str = ""

    def __post_init__(self) -> None:
        if (self.value is None) == (not self.unavailable):
            raise ValueError(
                "a Measured is a value OR a reason there is none. Got "
                f"value={self.value!r} unavailable={self.unavailable!r}. "
                "A value with a reason attached, or neither, is the "
                "half-populated state SPEC.md §6b.1a says cannot exist here.")

    @classmethod
    def absent(cls, reason: str) -> "Measured":
        if not reason:
            raise ValueError("an absent Measured must name why. A blank reason "
                             "renders as a blank, which is the defect.")
        return cls(value=None, unavailable=reason)

    @property
    def ok(self) -> bool:
        return self.value is not None


# ---- range budget — SPEC.md §6b.1a ----------------------------------------


def adr_pct(dailies: Sequence[Bar], n: int = ADR_DEFAULT_N) -> Measured:
    """`mean over N days of (high/low - 1) × 100`, **excluding today.**

    Kullamägi's TC2000 formula, verbatim. **NOT ATR** — it ignores gaps
    entirely, which is precisely the difference, and the two may never share a
    label.

    `dailies` is oldest-first and **includes today**, which this drops. Passing
    a series that already excludes today silently shifts the window by one day,
    so the caller's contract is stated here rather than assumed.
    """
    if len(dailies) < n + 1:
        return Measured.absent(
            f"need {n + 1} daily bars, have {len(dailies)}")
    window = dailies[-(n + 1):-1]          # excluding today
    ratios = []
    for b in window:
        if b.low <= 0:
            return Measured.absent(f"non-positive low in {b.ts}")
        ratios.append((b.high / b.low - 1) * 100)
    return Measured(value=statistics.fmean(ratios),
                    sample=f"{n} sessions, excl. today")


def adr_dollar(adr_percent: Measured, todays_open: float) -> Measured:
    """`ADR% × today's open / 100`."""
    if not adr_percent.ok:
        return Measured.absent(adr_percent.unavailable)
    if todays_open <= 0:
        return Measured.absent("no opening print")
    return Measured(value=adr_percent.value * todays_open / 100,
                    sample=adr_percent.sample)


def adr_used(current: float, todays_open: float, adr_dol: Measured) -> Measured:
    """`(current - open) / ADR$`, as a percentage. **Over 100 % renders `OVER`**
    — that is the renderer's job; this returns the number that produces it."""
    if not adr_dol.ok:
        return Measured.absent(adr_dol.unavailable)
    if adr_dol.value == 0:
        return Measured.absent("ADR $ is zero")
    return Measured(value=abs(current - todays_open) / adr_dol.value * 100,
                    sample=adr_dol.sample)


def room_left(current: float, todays_open: float, adr_dol: Measured) -> tuple[Measured, Measured]:
    """Distance to a full ADR, **both directions.** Returns `(up, down)`.

    Both, because a name that has used 90 % of its budget upward has very
    little room up and a great deal down, and one number cannot say that.
    """
    if not adr_dol.ok:
        return Measured.absent(adr_dol.unavailable), Measured.absent(adr_dol.unavailable)
    up = todays_open + adr_dol.value - current
    down = current - (todays_open - adr_dol.value)
    return (Measured(value=up, sample=adr_dol.sample),
            Measured(value=down, sample=adr_dol.sample))


# ---- ATR — a DIFFERENT quantity, and it says so ---------------------------


def true_ranges(dailies: Sequence[Bar]) -> list[float]:
    """`max(H-L, |H-C_prev|, |L-C_prev|)`.

    **True Range uses the prior close, including the gap.** That is the whole
    difference from ADR, which ignores gaps — and it is why substituting one for
    the other is never a rounding matter.
    """
    out = []
    for prev, cur in zip(dailies, dailies[1:]):
        out.append(max(cur.high - cur.low,
                       abs(cur.high - prev.close),
                       abs(cur.low - prev.close)))
    return out


def atr_d14(dailies: Sequence[Bar], n: int = ATR_DEFAULT_N) -> Measured:
    """Wilder's ATR — **RMA-smoothed, α = 1/n.**

    **NOT a simple mean of the last n true ranges**, which is the most common
    way this is implemented wrong and which agrees with the correct value often
    enough to survive a spot check.

    Seeded with the mean of the first `n` true ranges, then
    `atr = (atr * (n - 1) + tr) / n` — Wilder's own recursion.
    """
    trs = true_ranges(dailies)
    if len(trs) < n:
        return Measured.absent(f"need {n + 1} daily bars, have {len(dailies)}")
    atr = statistics.fmean(trs[:n])
    for tr in trs[n:]:
        atr = (atr * (n - 1) + tr) / n
    return Measured(value=atr, sample=f"Wilder RMA, n={n}, {len(trs)} true ranges")


# ---- the SMA stack, and extension in ADR units ----------------------------


def sma(dailies: Sequence[Bar], n: int) -> Measured:
    if len(dailies) < n:
        return Measured.absent(f"need {n} daily bars, have {len(dailies)}")
    return Measured(value=statistics.fmean(b.close for b in dailies[-n:]),
                    sample=f"{n}-day SMA")


def extension_in_adr(price: float, sma_value: Measured, adr_dol: Measured) -> Measured:
    """How far price sits above the moving average, **in ADR units.**

    Percent would be the obvious unit and is the wrong one: 8 % is a normal
    Tuesday on one name and a three-sigma event on another. ADR units normalise
    by the name's own daily range, which is what makes two symbols comparable.
    """
    if not sma_value.ok:
        return Measured.absent(sma_value.unavailable)
    if not adr_dol.ok:
        return Measured.absent(adr_dol.unavailable)
    if adr_dol.value == 0:
        return Measured.absent("ADR $ is zero")
    return Measured(value=(price - sma_value.value) / adr_dol.value,
                    sample=f"{sma_value.sample} / ADR $")


# ---- VWAP — ONE basis, per S010 part 0 ------------------------------------


def vwap_from_bars(minutes: Sequence[Bar]) -> Measured:
    """`Σ(Bar.WAP × volume) ÷ Σ(volume)`. **One basis, no alternative.**

    S010 part 0 resolves `BUILD-PLAN.md` §010's contradiction in favour of
    `2c-bis`: the tick-derived variant is retired, and with it the
    `tick budget exhausted` state, the 1,000-tick pagination and the
    boundary-second dedup. **None of them is built.**

    **The label still renders, and it is never a fallback.** One basis means
    nothing to declare per row, nothing to substitute, and nothing for two
    correct options to disagree about.

    A bar with no `wap` **refuses**. Substituting `close` would produce a
    number that looks like a VWAP, is wrong inside any minute where price moved,
    and is most wrong on the fast one-sided minutes that matter — and it is a
    stop level, so it lands in the position size.
    """
    total_v = 0.0
    total_pv = 0.0
    for b in minutes:
        if b.wap is None:
            return Measured.absent("bar without WAP — refusing to substitute close")
        total_v += b.volume
        total_pv += b.wap * b.volume
    if total_v <= 0:
        return Measured.absent("no volume yet")
    span = f"{minutes[0].ts} to {minutes[-1].ts}" if minutes else "no bars"
    return Measured(value=total_pv / total_v,
                    sample=f"bar-derived · {total_v:,.0f} sh · {len(minutes)} min · {span}")


def cumulative_volume(minutes: Sequence[Bar]) -> Measured:
    if not minutes:
        return Measured.absent("no bars")
    return Measured(value=sum(b.volume for b in minutes),
                    sample=f"{len(minutes)} min from {minutes[0].ts}")


# ---- RVOL — SPEC.md §8.4, exactly two ------------------------------------


def rvol_curve(sessions: Sequence[Sequence[Bar]]) -> dict[str, float]:
    """**The denominator is a CURVE, not a number** — one median cumulative
    volume per minute of the session, over the last N sessions.

    **Median, not mean.** One earnings day in a 20-session window inflates a
    mean reference across the whole curve and silently deflates today's reading
    at every minute, not just at one.

    Keyed by clock time (`HH:MM`), because the comparison is always at the same
    clock time: 400k shares by 09:31 and 400k by 11:00 are not the same event,
    and a full-day ratio cannot tell them apart.
    """
    per_minute: dict[str, list[float]] = {}
    for session in sessions:
        running = 0.0
        for b in session:
            running += b.volume
            per_minute.setdefault(_clock(b.ts), []).append(running)
    return {k: statistics.median(v) for k, v in per_minute.items()}


def _clock(ts: str) -> str:
    """`HH:MM` out of an ISO timestamp."""
    return ts[11:16] if len(ts) >= 16 else ts


def rvol_at(today: Sequence[Bar], curve: dict[str, float],
            sessions_used: int = RVOL_SESSIONS) -> Measured:
    """`cumulative volume to t ÷ median cumulative volume to t`.

    **Carries `t` in its sample, always.** Two readings at different `t` do not
    compare, and the display makes that unmissable by never dropping the time.
    """
    if not today:
        return Measured.absent("no bars today")
    t = _clock(today[-1].ts)
    ref = curve.get(t)
    if ref is None:
        return Measured.absent(f"no {sessions_used}-session reference for {t}")
    if ref <= 0:
        return Measured.absent(f"zero reference volume at {t}")
    cum = sum(b.volume for b in today)
    return Measured(value=cum / ref,
                    sample=f"{t} · {sessions_used}d median")


def rvol_rel(symbol: Measured, sector: Optional[Measured]) -> Measured:
    """`RVOL_t(symbol) ÷ RVOL_t(sector ETF)` — is *this name* busy, or is the
    whole sector busy.

    **No sector mapping refuses BY NAME. It never renders `1.0`.** A neutral
    number for a missing input is the exact defect this project exists to
    prevent: `1.0` reads as *"in line with its sector"*, which is a finding,
    when the truth is that nothing was compared at all.
    """
    if sector is None:
        return Measured.absent("no sector mapping")
    if not symbol.ok:
        return Measured.absent(symbol.unavailable)
    if not sector.ok:
        return Measured.absent(sector.unavailable)
    if sector.value == 0:
        return Measured.absent("sector RVOL is zero")
    return Measured(value=symbol.value / sector.value,
                    sample=f"vs sector · {symbol.sample}")


# ---- the level rail -------------------------------------------------------


def round_numbers(price: float, span: float) -> list[float]:
    """Whole and half dollars within `span` of price. **Not a prediction** —
    a rail entry is a place other people have resting orders, nothing more."""
    if span <= 0:
        return []
    lo, hi = price - span, price + span
    out, x = [], (int(lo * 2) / 2)
    while x <= hi:
        if x >= lo:
            out.append(round(x, 2))
        x += 0.5
    return out


def level_rail(*, prev_day: Optional[Bar], premarket: Sequence[Bar],
               opening_range: Sequence[Bar], vwap: Measured,
               year_high: Optional[float], year_low: Optional[float],
               price: float, adr_dol: Measured) -> dict[str, Measured]:
    """PDH/PDL · PMH/PML · ORH/ORL · session VWAP · 52-week · round numbers.

    **Every entry that cannot be computed names why.** A rail with silent gaps
    is worse than a short rail, because the gap looks like open space.
    """
    def hi_lo(bars: Sequence[Bar], what: str) -> tuple[Measured, Measured]:
        if not bars:
            return Measured.absent(f"no {what} bars"), Measured.absent(f"no {what} bars")
        return (Measured(value=max(b.high for b in bars), sample=f"{len(bars)} {what} bars"),
                Measured(value=min(b.low for b in bars), sample=f"{len(bars)} {what} bars"))

    pmh, pml = hi_lo(premarket, "pre-market")
    orh, orl = hi_lo(opening_range, "opening-range")
    span = adr_dol.value if adr_dol.ok else 0.0
    return {
        "PDH": Measured(value=prev_day.high, sample="prior session") if prev_day
               else Measured.absent("no prior session bar"),
        "PDL": Measured(value=prev_day.low, sample="prior session") if prev_day
               else Measured.absent("no prior session bar"),
        "PMH": pmh, "PML": pml, "ORH": orh, "ORL": orl,
        "VWAP": vwap,
        "52wH": Measured(value=year_high, sample="52 weeks") if year_high is not None
                else Measured.absent("no 52-week high"),
        "52wL": Measured(value=year_low, sample="52 weeks") if year_low is not None
                else Measured.absent("no 52-week low"),
        "round": Measured(value=float(len(round_numbers(price, span))),
                          sample=f"±{span:.2f} of {price:.2f}") if span > 0
                 else Measured.absent("no ADR $ to span"),
    }

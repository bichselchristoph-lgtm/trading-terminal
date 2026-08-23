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
from enum import Enum
from typing import Iterable, Optional, Sequence

#: `SPEC.md` §6b.1a — Kullamägi's convention. **20, not 14.** TradingView's
#: built-in ADR and its screener ADR% both use 14 and a different estimator;
#: crossing the two produces disagreement before session definitions are even in
#: play. Named and versioned rather than inline, per the threshold convention.
ADR_DEFAULT_N = 20

#: Wilder's period. `atr_d14` is what the 3×ATR stop floor consumes.
#: **20, not 14 — B-091, ruled twice and confirmed directly by Christoph on
#: 2026-08-22: there is one ATR, it is 20-day, and it is ETH.** The function
#: keeps its `atr_d14` name (renaming it is a larger, unscoped change reaching
#: every caller and docstring that says "Wilder's ATR" generically); the
#: rendered label changes from `ATR14` to `ATR20` at the two places that name
#: it for a reader — `live/attach/attach.py`'s context key and
#: `live/tui/app.py`'s `CONTEXT_ORDER`.
ATR_DEFAULT_N = 20

#: §8.4 — the RVOL denominator is a curve over the last N sessions.
RVOL_SESSIONS = 20


# ---- session basis — 038 Part 1 -------------------------------------------
#
# **A basis is a definition, not a setting, and that is why it lives here.**
#
# `SPEC.md` §4.4 says no setting lives in code — not a threshold, not a window,
# not `useRTH`. **A session basis is EXEMPT, and the exemption is written down
# here because an exemption that is not written down is one that gets undone.**
# `036` proposed putting these in `config/indicators.yaml`; `038` overrules it.
#
# The distinction: **a setting is a choice somebody could sensibly make
# differently. A basis is a fact about what the indicator IS.** ADR is the mean
# of each session's own high-low with no gap term, so it is the regular session
# by definition — a config key implying otherwise invites someone to flip it in a
# hurry, and the number keeps its name while changing what it measures.
#
# So the value that reaches the request comes from the constant declared beside
# the indicator's own definition. **Never a literal at the call site, never
# `config/`.** `tests/test_session_basis.py` asserts the request actually issued
# carries the constant's flag, not merely that the constant exists.


@dataclass(frozen=True)
class SessionBasis:
    """Which bars an indicator is computed over, and why it is those bars.

    `label` is rendered on the row. **That is the point of the type** — 038
    Part 4: *a value that carries its basis can be compared with something; a
    value that does not can only be argued about.* ADR and ATR sit four rows
    apart, are both labelled volatility, and are computed on different sessions
    **on purpose**; without the label a reader compares them.

    `why` is carried so the reason is reachable from code and from a test, not
    only from a comment a reader's eye passes over.
    """

    #: What `reqHistoricalData(useRTH=...)` is given. **No default** — the whole
    #: defect class here is a flag that acquired one.
    use_rth: bool
    #: The window, in ET, as it renders: `09:30-16:00 ET`.
    label: str
    #: Why it is this window and not the other.
    why: str


#: **ADR is a STATISTIC and it is RTH by definition.** Average *Day* Range is the
#: mean of each session's own `High - Low` and **has no gap term** — that is what
#: distinguishes it from ATR. So it measures the session actually traded.
#:
#: **It will NOT match a TWS "ADR" computed over 04:00-20:00 bars, and that is
#: correct rather than a defect.** TWS has no native ADR at all; anything it
#: shows comes from a different computation over a different bar set.
ADR_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="Average DAY Range: the mean of each session's own high-low, with no "
        "gap term. RTH by definition, not by preference.")

#: **ATR is a STATISTIC and it is ETH.** Average *True* Range is
#: `max(H-L, |H-Cprev|, |Cprev-L|)` — **the gap across the prior close is part of
#: the measurement**, so it must be computed on the bar series whose
#: close-to-close relationship is the real one.
#:
#: This is the flag that was wrong. `c015`/`013` measured `ATR14` at `13.14`
#: against Christoph's TWS daily ATR(14) of ~`15.6` — **-16 %, and ATR feeds the
#: 3xATR stop floor, which feeds every share count.** A well-formed number with
#: no flag on it.
ATR_BASIS = SessionBasis(
    use_rth=False, label="04:00-20:00 ET",
    why="Average TRUE Range: the true range spans the prior close, so the gap "
        "is part of the measurement. ETH.")

#: **PDH/PDL are LEVELS, not statistics, and they are RTH.** 038 Part 1, and this
#: is the half `036` got wrong.
#:
#: **If they were ETH, then on any day the extreme occurred outside 09:30-16:00,
#: `PDL` IS `AML`** — one number, two names, and no way to tell which you are
#: looking at. A level that silently changes identity depending on when the
#: extreme happened is the canonical defect of this project.
#:
#: Confirmed on Christoph's own QQQ chart for 2026-08-13: the session low of
#: `722.34` sits in the early pre-market, so an ETH `PDL` would have been `PML`
#: that day. **`036` would have pinned `PDL 717.37` — the ETH low, and therefore
#: the `AML` — into the first externally-checked fixture this project has.**
#:
#: **ADR being RTH does not propagate here and ATR being ETH does not either.**
#: Different kinds of object: a level exists because price traded there, in a
#: named window, **and the window is part of the name.**
PRIOR_DAY_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="A prior-day level is the prior REGULAR session's extreme. On ETH bars "
        "PDL would collapse into AML whenever the low fell after 16:00.")

#: **VWAP, cumulative volume and RVOL: ETH, anchored 04:00.** Settled before 038
#: and carried forward unchanged — `008b` measured that liquid names do have
#: pre-market volume, and on a gapper that has done 2M shares before the open the
#: pre-market VWAP is where the level sits at 09:31.
#:
#: **RVOL must match ITSELF**: today's numerator and the 20-session denominator
#: on the same basis. An RTH curve against an ETH numerator has no key past the
#: close, which is how the mismatch announced itself rather than rendering a
#: plausible ratio.
INTRADAY_BASIS = SessionBasis(
    use_rth=False, label="04:00-20:00 ET",
    why="Session VWAP, cumulative volume and the RVOL curve all include "
        "pre-market and anchor at 04:00 ET. Both sides of RVOL share this.")

#: **NOT RULED BY 038, and left exactly as it was found.** 038 Part 1's table
#: names PDC, PDO, PDH/PDL, PMH/PML, AMH/AML and ORH/ORL, and its statistic
#: distinction covers ADR and ATR. **The SMA stack is neither a level nor one of
#: the two statistics it rules on, so nothing in 038 decides this.**
#:
#: `036` said ETH — but `036` is superseded, and `038` did not carry that row
#: forward. **Changing it on the strength of a superseded document is exactly the
#: failure this project keeps having**, so it keeps the RTH basis it already had
#: and the gap is reported in the done-note rather than closed by inference.
#:
#: **041 looked at this again and DELIBERATELY LEFT IT UNRULED.** *"Ruling a
#: value nothing reads is admin."* It must be ruled **before anything consumes
#: it** — `OBS-051`, which 041 narrows to the SMA stack alone rather than
#: closing.
#:
#: **041's stated reason for leaving it does not hold in this tree, and the
#: conclusion survives anyway.** 041 says `OBS-051`'s argument — that an ETH SMA
#: would put the two sides of the `ext` ratio on different bases — is void
#: because *"`ext` no longer exists"*. **It does exist**: `ext 10/20/50` are still
#: in `CONTEXT_ORDER` and still computed by `extension_in_adr`, because the scope
#: decision of 2026-08-14 is a decision and `S012` has not been built. So the
#: original argument still stands, and it points the same way: `ADR $` is RTH
#: under `038`, so an ETH SMA would divide across two bases.
SMA_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="UNRULED by 038 and deliberately left unruled by 041 -- nothing should "
        "rule a value nothing reads. Must be ruled before anything consumes it.")

# ---- the thirteen remaining levels — 041, and they are all RTH -------------
#
# **Christoph's ruling, 2026-08-15. Closes `OBS-051`.** `038` ruled the day,
# pre-market, post-market and opening-range levels and left thirteen undeclared;
# **they kept whatever basis they happened to have, which is not a decision.**
#
# **The argument is COMPOSITION, and it is stronger than the thin-print one.**
# `PWH` is the highest price of the prior week, so it must be the maximum of that
# week's `PDH`s. `MoMH` must be the maximum of the weeks. `52wH` the maximum of
# the months. **`038` made `PDH` RTH — so if `PWH` were ETH the chain stops
# composing**, and you get a week whose high is above every day inside it with no
# row on the panel able to explain why. Break the chain anywhere and the level
# rail stops being one structure.
#
# **The thin-print argument reaches the same conclusion and is weaker, so it is
# recorded second:** a handful of odd lots at 03:00 should not set a price a
# position is sized against.
#
# **The cost is real, accepted, and must not be "fixed" later.** `52wH`, `52wL`
# and `ATH` **will not match Christoph's TradingView chart** on any name whose
# extreme printed outside regular hours, and he trades with ETH charts enabled.
# On QQQ they agree today; on a gap-and-fade small cap they will not. **A
# disagreement there is the ruling working, not a defect** — `OBS-053`.

#: **`HOD` / `LOD`.** This is the `PDL` argument exactly: an ETH `HOD` on a
#: gap-down morning **is** `PMH` — one price, two names, and no way to tell which
#: you are looking at. A level that can silently become another level is the
#: defect `038` exists to remove.
TODAY_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="HOD/LOD are regular-session extremes. On ETH bars a gap-down morning's "
        "HOD is PMH, which is one price wearing two names.")

#: **`PWH` / `PWL` / `PWO` / `PWC`.** The week composes out of its days.
#: `PWO` and `PWC` follow automatically — a week's open is its first day's open
#: and its close is its last day's close, and both are already RTH auction prints
#: under `038`.
PRIOR_WEEK_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="A week's high must be the maximum of its days' PDHs. 038 made PDH RTH, "
        "so an ETH week would sit above every day inside it.")

#: **`MoMH` / `MoML` / `MoMO` / `MoMC`.** The month composes out of the weeks,
#: for the same reason and by the same chain.
PRIOR_MONTH_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="A month's high must be the maximum of its weeks. Same composition "
        "chain as PRIOR_WEEK_BASIS, one level up.")

#: **`52wH` / `52wL` / `ATH`.** The top of the same chain — the year is the
#: maximum of its months.
#:
#: **Renamed from `YEAR_BASIS` under 041**, because `ATH` is not a year and the
#: old name would have been wrong for a third of what it now serves.
LONG_BASIS = SessionBasis(
    use_rth=True, label="09:30-16:00 ET",
    why="52wH/52wL/ATH are the top of the composition chain: the year is the "
        "maximum of its months. RULED RTH by 041, and deliberately divergent "
        "from an ETH TradingView chart — see OBS-053.")


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


class Unit(str, Enum):
    """What kind of quantity a number is. **038 Part 2: all numbers need units.**

    **The producer declares it, not the renderer.** Whether `13.14` is dollars or
    a multiple is a fact about the indicator, and a renderer that guessed from
    the row's name would be re-deriving something the computation already knew.

    `live/tui/numbers.py` maps these onto a format; the PRECISION for each comes
    from `config/formatting.yaml`, per `SPEC.md` §4.0a — *one function, and its
    precision comes from config.* **Precision is a genuine setting and stays in
    config; a session basis is not and stays in code** (`SessionBasis`). That is
    the same distinction 038 Part 3 draws, applied in both directions.
    """

    #: Prices, distances and dollar ranges. `$` prefix, 2 decimals.
    DOLLAR = "dollar"
    #: `%`, 1 decimal. **The referent is named in `sample`** — 038 Part 2:
    #: `78% of $1.29`, never a bare `78%`.
    PERCENT = "percent"
    #: A distance expressed in ADR units. `1.4 ADR`, 1 decimal.
    ADR = "adr"
    #: A ratio or multiple. `6.1×`, 1 decimal, **and the baseline named** in
    #: `sample` — `6.1×` alone is the `12.4M` complaint again.
    MULTIPLE = "multiple"
    #: Share counts. `sh` suffix, whole, thousands-separated.
    SHARES = "shares"
    #: A count of things. Whole. Renders its noun, because a bare integer on a
    #: price rail reads as a price — see `round`, 038 Part 6 row 2.
    COUNT = "count"


@dataclass(frozen=True)
class Measured:
    """A number, **or a named reason there is none.** Never both, never neither.

    `sample` is what it was computed over — `20 sessions`, `18.4M sh · 42 min ·
    from 09:30:00`. S010 requires it on every rendered value.

    `unit` and `basis` are 038's additions and they are **required on every value
    that renders**. A number with neither is the defect 038 exists to close: it
    took a UAT and four chart screenshots to settle what one field in the detail
    column answers permanently.
    """

    value: Optional[float]
    sample: str = ""
    unavailable: str = ""
    #: 038 Part 2. Blank only on an absent `Measured`, which renders a reason.
    unit: Unit = Unit.DOLLAR
    #: 038 Part 1/4 — the session this was computed over, or a clock anchor for
    #: a value that is anchored rather than session-scoped. **`None` is legal
    #: only where the quantity genuinely has no session** (a pure count), and the
    #: renderer refuses anything else that arrives without one.
    basis: Optional["SessionBasis"] = None

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
                    sample=f"{n} sessions, excl. today · of each session's low",
                    unit=Unit.PERCENT, basis=ADR_BASIS)


def adr_dollar(adr_percent: Measured, todays_open: float) -> Measured:
    """`ADR% × today's open / 100`."""
    if not adr_percent.ok:
        return Measured.absent(adr_percent.unavailable)
    if todays_open <= 0:
        return Measured.absent("no opening print")
    return Measured(value=adr_percent.value * todays_open / 100,
                    sample=adr_percent.sample,
                    unit=Unit.DOLLAR, basis=ADR_BASIS)


def adr_used(current: float, todays_open: float, adr_dol: Measured) -> Measured:
    """`(current - open) / ADR$`, as a percentage. **070/`ATTACHED` mockup v1.0:
    the number renders past 100 %, uncapped — a day whose range exceeds its
    20-session average is ordinary, and only the accompanying bar clamps at
    full.** (An earlier docstring here said the renderer would print the word
    `OVER` instead; that was never built and 070 rules it out explicitly —
    corrected rather than left to mislead the next reader.)"""
    if not adr_dol.ok:
        return Measured.absent(adr_dol.unavailable)
    if adr_dol.value == 0:
        return Measured.absent("ADR $ is zero")
    return Measured(value=abs(current - todays_open) / adr_dol.value * 100,
                    # **The referent, named.** 038 Part 2: never a bare `78%`.
                    # And 038 Part 6 row 1 asked what this anchors to -- it is
                    # TODAY'S OPEN, stated here so the row itself answers it.
                    sample=f"of ${adr_dol.value:,.2f} · from today's open · "
                           f"{adr_dol.sample}",
                    unit=Unit.PERCENT, basis=ADR_BASIS)


def adr_available(current: float, todays_open: float, adr_dol: Measured) -> Measured:
    """**042 Part 3. The one row that replaces four.**

    `ADR used`, `ADR $`, `room up` and `room down` leave the panel (c015 §1.7).
    What replaces them is *the percentage of the day's average range still
    available*, which is the reading Christoph actually takes.

    **`room up` and `room down` measured the same quantity in dollars and
    invited being read as `clear for`** — distance to the next obstacle — which
    is a different question entirely. That confusion is the reason for the
    deletion, not screen space.

    **`ADR` itself is not deleted.** It stays RTH, it stays the denominator for
    every ADR-expressed distance, and `round`'s span still consumes `ADR $`.
    Only the display rows go.

    **NOT CLAMPED AT ZERO, deliberately.** A name that has travelled 130 % of
    its average range returns `-30 %`, and that is the honest number: it says
    *past the budget and by how much*. Clamping would render the most
    informative case identically to the merely-exhausted one.
    """
    used = adr_used(current, todays_open, adr_dol)
    if not used.ok:
        return Measured.absent(used.unavailable)
    return Measured(value=100.0 - used.value,
                    # The referent, named — 038 Part 2 forbids a bare `36%`.
                    sample=f"of ${adr_dol.value:,.2f} · from today's open · "
                           f"{adr_dol.sample}",
                    unit=Unit.PERCENT, basis=ADR_BASIS)


def room_left(current: float, todays_open: float, adr_dol: Measured) -> tuple[Measured, Measured]:
    """Distance to a full ADR, **both directions.** Returns `(up, down)`.

    Both, because a name that has used 90 % of its budget upward has very
    little room up and a great deal down, and one number cannot say that.

    **042 Part 3 DELETED BOTH ROWS FROM THE PANEL, AND THIS FUNCTION NOW HAS NO
    CALLER.** It is kept rather than removed for one reason: the argument in the
    paragraph above is correct and is the kind that gets re-derived badly. What
    is *wrong* with the rows is not the arithmetic — it is that **they measured
    the same quantity as `ADR used` in dollars and invited being read as
    `clear for`**, which is distance to the next obstacle and a different
    question entirely.

    **Do not re-add them to `CONTEXT_ORDER`.** If `clear for` needs distance
    arithmetic when `S012` builds the level rail, it needs distance to the next
    *level*, which is not this function.
    """
    if not adr_dol.ok:
        return Measured.absent(adr_dol.unavailable), Measured.absent(adr_dol.unavailable)
    up = todays_open + adr_dol.value - current
    down = current - (todays_open - adr_dol.value)
    # **Anchored on TODAY'S OPEN**, which is 038 Part 6 row 1's question. Said
    # in the sample rather than left for a reader to reverse-engineer from the
    # arithmetic, which is how it came to be asked.
    anchor = f"to a full ADR from today's open · {adr_dol.sample}"
    return (Measured(value=up, sample=anchor, unit=Unit.DOLLAR, basis=ADR_BASIS),
            Measured(value=down, sample=anchor, unit=Unit.DOLLAR, basis=ADR_BASIS))


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
    return Measured(value=atr,
                    sample=f"Wilder RMA, n={n}, {len(trs)} true ranges",
                    unit=Unit.DOLLAR, basis=ATR_BASIS)


# ---- the SMA stack, and extension in ADR units ----------------------------


def sma(dailies: Sequence[Bar], n: int) -> Measured:
    if len(dailies) < n:
        return Measured.absent(f"need {n} daily bars, have {len(dailies)}")
    return Measured(value=statistics.fmean(b.close for b in dailies[-n:]),
                    sample=f"{n}-day SMA", unit=Unit.DOLLAR, basis=SMA_BASIS)


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
                    sample=f"{sma_value.sample} / ADR $",
                    unit=Unit.ADR, basis=sma_value.basis)


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
                    sample=f"bar-derived · {total_v:,.0f} sh · {len(minutes)} min "
                           f"· 04:00 anchor · {span}",
                    unit=Unit.DOLLAR, basis=INTRADAY_BASIS)


def cumulative_volume(minutes: Sequence[Bar]) -> Measured:
    if not minutes:
        return Measured.absent("no bars")
    return Measured(value=sum(b.volume for b in minutes),
                    sample=f"{len(minutes)} min · 04:00 anchor · "
                           f"from {minutes[0].ts}",
                    unit=Unit.SHARES, basis=INTRADAY_BASIS)


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
                    sample=f"vs {sessions_used}d median at {t}h ET",
                    unit=Unit.MULTIPLE, basis=INTRADAY_BASIS)


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
                    sample=f"vs sector RVOL · {symbol.sample}",
                    unit=Unit.MULTIPLE, basis=INTRADAY_BASIS)


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
               opening_5: Sequence[Bar], opening_15: Sequence[Bar],
               session_clock: Optional[str], vwap: Measured,
               year_high: Optional[float], year_low: Optional[float],
               price: float, adr_dol: Measured) -> dict[str, Measured]:
    """PDH/PDL · PMH/PML · ORH5/ORL5 · ORH15/ORL15 · VWAP · 52-week · rounds.

    **Every entry that cannot be computed names why.** A rail with silent gaps
    is worse than a short rail, because the gap looks like open space.

    ----

    **042 Part 1: the opening range is TWO windows, and a bare `ORH` is gone.**
    `038` v1.0 named `ORH`/`ORL` and there are four levels — 09:30–09:35 and
    09:30–09:45. A bare `ORH` is a well-formed name answering two different
    questions, which is this project's defining defect, so it does not survive
    anywhere. **Every bare `ORH`/`ORL` in this tree meant the 5-minute window**
    — the caller sliced `09:30 <= t < 09:35` and nothing else ever existed — so
    the rename carried no ambiguity to resolve. Recorded in `042`'s done-note.

    **Both are RTH by definition** and `041` does not change that: the opening
    range is a regular-session object.

    **`session_clock` is the newest bar's ET start time, and it is what makes
    the refusal possible.** Without it a 15-minute range computed at 09:37 is a
    7-minute range wearing a 15-minute name — a partial window rendering as a
    complete one, with a plausible number in it.
    """
    def hi_lo(bars: Sequence[Bar], what: str,
              window: str) -> tuple[Measured, Measured]:
        """**A clock-defined window states which bars it sliced** (038 Part 1).

        `PMH/PML` and `ORH/ORL` are defined by wall-clock time, not by the RTH
        flag — but they are sliced out of the ETH minute series, and *which
        series* is exactly what `034` got wrong when UTC stamps put the opening
        range at 05:30 ET. So the window and the basis both render.
        """
        if not bars:
            return Measured.absent(f"no {what} bars"), Measured.absent(f"no {what} bars")
        sample = f"{len(bars)} {what} bars · {window}"
        return (Measured(value=max(b.high for b in bars), sample=sample,
                         unit=Unit.DOLLAR, basis=INTRADAY_BASIS),
                Measured(value=min(b.low for b in bars), sample=sample,
                         unit=Unit.DOLLAR, basis=INTRADAY_BASIS))

    def opening(bars: Sequence[Bar], window: str,
                final_minute: str) -> tuple[Measured, Measured]:
        """**Refuses a partial range rather than rendering one** — 042's exit
        refusal, and `038`'s rule that a level carries its validity time.

        `final_minute` is the START of the window's last one-minute bar: 09:34
        closes 09:30–09:35, 09:44 closes 09:30–09:45. The window is complete
        once a bar starting then exists, so the comparison is `>=` against the
        newest bar's clock. **This assumes one-minute bars**, which is what the
        whole intraday path assumes — `_clock` slices `ts[11:16]` and every
        caller passes minutes.

        Counting bars instead would be wrong on a thin name: a minute with no
        trades produces no bar, and fifteen-minus-one bars is a closed window
        with a quiet minute in it, not an open one.
        """
        if session_clock is None:
            return (Measured.absent("no session bars — window not closed"),
                    Measured.absent("no session bars — window not closed"))
        if session_clock < final_minute:
            why = f"window not closed — {window} needs {final_minute}, session at {session_clock}"
            return Measured.absent(why), Measured.absent(why)
        return hi_lo(bars, "opening-range", window)

    pmh, pml = hi_lo(premarket, "pre-market", "04:00-09:30 ET, today")
    orh5, orl5 = opening(opening_5, "09:30-09:35 ET, today", "09:34")
    orh15, orl15 = opening(opening_15, "09:30-09:45 ET, today", "09:44")
    span = adr_dol.value if adr_dol.ok else 0.0
    # **`round` is a COUNT, and 038 Part 6 row 2 is right that the label does not
    # say so.** The row computes `len(round_numbers(...))` — how MANY half-dollar
    # levels fall within +/-ADR$ of price — and rendered it through the same
    # 2-decimal price formatter as every other rail row, producing `47.00` on a
    # 733 instrument. Nothing near 47 is a round level for QQQ.
    #
    # **Fixed here by making the unit honest rather than by renaming the row** —
    # 038 puts panel layout out of scope. `Unit.COUNT` renders `47 levels`, which
    # cannot be misread as a price. The label question is reported, not decided.
    return {
        "PDH": Measured(value=prev_day.high, sample="prior session",
                        unit=Unit.DOLLAR, basis=PRIOR_DAY_BASIS) if prev_day
               else Measured.absent("no prior session bar"),
        "PDL": Measured(value=prev_day.low, sample="prior session",
                        unit=Unit.DOLLAR, basis=PRIOR_DAY_BASIS) if prev_day
               else Measured.absent("no prior session bar"),
        "PMH": pmh, "PML": pml,
        "ORH5": orh5, "ORL5": orl5, "ORH15": orh15, "ORL15": orl15,
        "VWAP": vwap,
        "52wH": Measured(value=year_high, sample="52 weeks", unit=Unit.DOLLAR,
                         basis=LONG_BASIS) if year_high is not None
                else Measured.absent("no 52-week high"),
        "52wL": Measured(value=year_low, sample="52 weeks", unit=Unit.DOLLAR,
                         basis=LONG_BASIS) if year_low is not None
                else Measured.absent("no 52-week low"),
        "round": Measured(value=float(len(round_numbers(price, span))),
                          sample=f"half-dollar levels within ±${span:,.2f} "
                                 f"of ${price:,.2f}",
                          unit=Unit.COUNT, basis=None) if span > 0
                 else Measured.absent("no ADR $ to span"),
    }

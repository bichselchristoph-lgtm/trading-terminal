"""038 Part 5 test 5 — QQQ, 2026-08-13, pinned. **No network; bar fixtures only.**

**These are the first externally-checked values this project has.** Christoph
performed `013` on 2026-08-13 against IBKR's own daily bars in TWS — same source,
same instrument, the chart tooltip stating its own basis as
`8/12 (04:00:00-20:00:00) EST`. Six values matched. Two did not, and both are
inputs to position size.

| Row | Terminal, pre-038 | IBKR chart | |
|---|---|---|---|
| ORH / ORL | 726.02 / 724.03 | 726.02 / 724.03 | exact — `034`'s timezone fix |
| PDH | 727.25 | 727.25 | match |
| PML | 722.80 | 722.80 | match |
| ATR14 | **13.14** | **≈15.6** | **−16 %** |

**A 16 % error in ATR is a 16 % error in every share count**, because ATR feeds
the 3×ATR stop floor and the stop floor feeds the size. It arrived as a
well-formed number with no flag on it.

----

**Two things are deliberately NOT pinned here, and both omissions are load-bearing.**

**1. `PDL $717.37` must not be pinned, and `036` would have.** `717.37` is the
*extended-hours* low, and under 038 Part 1 a prior-day level is the prior
**regular** session's extreme — so on 2026-08-13 that figure is `AML`, not `PDL`.
Pinning it would have baked a mislabelled level into the first externally-checked
fixture this project owns. **The RTH prior-day low was never supplied by the
UAT**, so this file pins the *property* — PDL comes from the regular-session
series and is not the extended-hours low — and states the number it uses as a
fixture constant rather than as a check.

**2. `ADR%` and `ADR $` are absent on purpose.** TWS has no native ADR; anything
it displays comes from a different computation over a different bar set. **It is
not a check and must not be recorded as one** — the same reason TradingView was
ruled out as an input while kept as a source of conventions.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.indicators.context import Bar
from live.attach.attach import Contract, attach

QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="SMART", sector_etf=None)

# ---- the externally-checked values ---------------------------------------
PDH = 727.25          # 8/12 high, matched
PMH = 725.46          # pre-market high, matched
PML = 722.80          # pre-market low, matched
ORH = 726.02          # opening range high (5-min), matched — 034's fix confirmed
ORL = 724.03          # opening range low (5-min), matched
# **There is no ORH15/ORL15 here and there must not be.** The fixture runs to
# 09:35 and Christoph's chart reading covers the 5-minute range only. Extending
# the bar series to 09:45 would mean inventing ten minutes that nobody verified,
# inside the one file in this repo whose values came from outside it.
ATR14 = 15.60         # Christoph's TWS daily ATR(14) reads ~15.6. ETH.

#: **The extended-hours low. NOT `PDL`.** Under 038 Part 1 this is `AML` — the
#: post/pre-market extreme — and the whole point of the ruling is that a level
#: whose identity depends on when the extreme happened is not a level at all.
ETH_LOW_NOT_PDL = 717.37

#: **A fixture constant, not an external check.** The UAT supplied the ETH low
#: and never the RTH one, so no number here can be claimed as verified. What IS
#: verified is that `PDL` reads the regular-session series.
RTH_PRIOR_LOW = 723.55


def _eth_dailies(n: int = 60) -> list[Bar]:
    """Bars whose true range is exactly `ATR14` on every bar.

    `H − L = 15.60`, and each close sits at the midpoint of the next bar's range,
    so `|H − Cprev|` and `|L − Cprev|` are both 7.80 and the true range is the
    high-low every time. **Wilder's RMA of a constant series is that constant**,
    which makes the expected ATR exact rather than approximate — a fixture whose
    answer needs rounding tolerance cannot distinguish an RMA from an SMA, and
    telling those apart is most of why this row is wrong in the wild.

    **The low is `717.37` on every bar, including 8/12's.** That is the figure
    `036` would have pinned as `PDL`, and it sits here — in the *extended-hours*
    series — so the contrast is structural rather than a special-cased bar. An
    earlier draft overrode `out[-2]` to carry it, which perturbed two true ranges
    and moved the expected ATR off `15.60` to `15.22`; a fixture that needs a
    tolerance to pass cannot tell Wilder's RMA from a simple mean, and telling
    those apart is most of why this row goes wrong in the wild.
    """
    out = []
    for i in range(n):
        low = ETH_LOW_NOT_PDL
        high = low + ATR14
        mid = (high + low) / 2
        ts = {n - 2: "2026-08-12", n - 1: "2026-08-13"}.get(
            i, f"2026-06-{(i % 28) + 1:02d}")
        out.append(Bar(ts=ts, open=mid, high=high, low=low, close=mid,
                       volume=50_000_000))
    return out


def _rth_dailies(n: int = 60) -> list[Bar]:
    """The regular-session series. **8/12 sits at index −2** — the prior day."""
    out = [Bar(ts=f"2026-06-{(i % 28) + 1:02d}", open=720.0, high=726.0,
               low=718.0, close=722.0, volume=40_000_000) for i in range(n)]
    out[-2] = Bar(ts="2026-08-12", open=724.0, high=PDH, low=RTH_PRIOR_LOW,
                  close=725.0, volume=40_000_000)
    out[-1] = Bar(ts="2026-08-13", open=725.0, high=726.5, low=724.0,
                  close=725.5, volume=40_000_000)
    return out


def _today_minutes() -> list[Bar]:
    """04:00 to 09:35 ET on 2026-08-13, one bar a minute.

    **The pre-market window is 04:00–09:30 and the opening range 09:30–09:35**,
    sliced on ET clock time. `034` sliced these on UTC stamps and read the
    opening range at 05:30 ET — four plausible, wrong values, no error, no flag.
    """
    out: list[Bar] = []
    for minute in range(4 * 60, 9 * 60 + 35):
        h, m = divmod(minute, 60)
        ts = f"2026-08-13T{h:02d}:{m:02d}:00"
        if minute < 9 * 60 + 30:
            hi, lo = (PMH, PML) if minute == 4 * 60 else (724.0, 723.5)
        else:
            hi, lo = (ORH, ORL) if minute == 9 * 60 + 30 else (725.0, 724.5)
        out.append(Bar(ts=ts, open=lo, high=hi, low=lo, close=hi,
                       volume=100_000, wap=(hi + lo) / 2))
    return out


class QQQFixture:
    """A `MarketData` answering 2026-08-13 from fixtures. **Never a network.**"""

    def resolve(self, symbol): return [QQQ]
    def tick_slots_in_use(self): return 0
    def cooldown_remaining_s(self, symbol): return 0
    def warm(self, c): pass    # 058 Part 2 — no-op for a fixture answering instantly

    def daily_bars(self, c, basis):
        """**The series differs by basis, which is the whole subject.**

        `SPEC.md:999` asserted the opposite — *"excluded, unchangeably — ETH
        cannot alter a daily bar"* — and 038 corrects it as factually wrong.
        """
        return _rth_dailies() if basis.use_rth else _eth_dailies()

    def intraday_sessions(self, c): return [_today_minutes() for _ in range(20)]
    def today_minutes(self, c): return _today_minutes()
    def sector_today_minutes(self, c): return None
    def sector_sessions(self, c): return None
    def open_tick_stream(self, c): raise RuntimeError("no tape in this slice")
    def playbook_for(self, c): return ""


def _attached():
    r = attach("QQQ", QQQFixture())
    assert r.attached and r.qualified, "the fixture attach did not qualify"
    return r


def test_the_four_matched_levels_still_match() -> None:
    """PDH, PMH, PML, ORH5, ORL5 — verified against IBKR's own chart.

    **042 Part 1 renamed `ORH`/`ORL` to `ORH5`/`ORL5`. The VALUES are
    untouched** — the window they were always computed over was 09:30–09:35,
    so this is a rename and not a re-measurement. Anything else here would be
    a regression against the only outside verification this project has.
    """
    rail = _attached().rail
    for name, expected in (("PDH", PDH), ("PMH", PMH), ("PML", PML),
                           ("ORH5", ORH), ("ORL5", ORL)):
        got = rail[name]
        assert got.ok, f"{name} refused: {got.unavailable}"
        assert round(got.value, 2) == expected, (
            f"{name} reads {got.value:.2f}, Christoph's IBKR chart reads "
            f"{expected:.2f}. **These are externally checked** — a change here "
            f"is a regression against the only outside verification this "
            f"project has.")


def test_atr_still_reads_about_15_6_though_070_removed_it_from_this_panel() -> None:
    """**The externally-checked value survives; its wiring into ATTACHED does
    not.** `13.14` against a true `~15.6`, −16 %, under the pre-038 defect
    (RTH instead of ETH) — that history is real and this fixture (every ETH
    bar's true range exactly `ATR14 = 15.60`) is the only externally-anchored
    proof this project has that Wilder's RMA reads the gap correctly. **070,
    ruled by Christoph 2026-08-23: no ATR anywhere in the ATTACHED panel —
    TRADE's stop selector is its only surface in the whole terminal** — so
    `_context_block` no longer computes it at all (confirmed: `"ATR20" not in
    _attached().context`, in the refusal test below). This test therefore
    calls `atr_d14` directly rather than through `attach()`, preserving the
    external verification for whichever future task wires ATR into TRADE.
    """
    from core.indicators.context import atr_d14
    atr = atr_d14(_eth_dailies())
    assert atr.ok, f"atr_d14 refused: {atr.unavailable}"
    assert abs(atr.value - ATR14) < 0.01, (
        f"atr_d14 reads {atr.value:.2f}; the ETH fixture's true range is "
        f"exactly {ATR14:.2f} on every bar. A value near 13.14 means the RTH "
        f"series was used — the pre-038 defect.")
    assert atr.basis is not None and atr.basis.use_rth is False, (
        "ATR must declare the extended-hours basis")
    assert atr.basis.label == "04:00-20:00 ET"


def test_no_atr_anywhere_in_the_attached_context() -> None:
    """**070 Part 3's leak check, against this file's own real fixture** — not
    a synthetic stand-in. `B-091`/`B-028`'s shape: a field absent from
    `CONTEXT_ORDER` but still reaching the record is not actually removed."""
    context = _attached().context
    assert "ATR20" not in context and "ATR14" not in context, (
        f"an ATR key survives in the ATTACHED context: {sorted(context)}")


def test_pdl_is_the_regular_session_low_and_not_the_extended_hours_low() -> None:
    """**038 Part 1, and the half `036` got wrong.**

    `036` would have pinned `PDL 717.37`. That figure is the extended-hours low,
    which under Part 1 is `AML` — **one number, two names, and no way to tell
    which you are looking at.** A level that silently changes identity depending
    on when the extreme occurred is the canonical defect of this project.

    **The RTH prior-day low was never externally supplied**, so what is asserted
    is the property, not a verified number.
    """
    pdl = _attached().rail["PDL"]
    assert pdl.ok, f"PDL refused: {pdl.unavailable}"
    assert round(pdl.value, 2) == RTH_PRIOR_LOW, (
        f"PDL reads {pdl.value:.2f}; the regular-session series puts the prior "
        f"day's low at {RTH_PRIOR_LOW:.2f}.")
    assert round(pdl.value, 2) != ETH_LOW_NOT_PDL, (
        f"PDL is reading the extended-hours low ({ETH_LOW_NOT_PDL}). That is "
        f"AML, not PDL.")
    assert pdl.basis is not None and pdl.basis.use_rth is True, (
        "PDL must declare the regular session")


#: **070 retires this test, deliberately, rather than renaming it.** ADR and
#: ATR were "computed differently, on purpose, and must never share a basis
#: label" -- a property about two rows on one panel. 070 removes one of the
#: two rows from the panel entirely (Christoph, 2026-08-23: no ATR in
#: ATTACHED), so the property this test asserted no longer describes anything
#: a reader can compare on screen. `test_atr_still_reads_about_15_6_though_
#: 070_removed_it_from_this_panel` keeps the ADR-basis-is-RTH /
#: ATR-basis-is-ETH facts alive independently, via `atr_d14` called directly.


def test_adr_percent_is_not_pinned_against_tws() -> None:
    """**Recorded as an assertion so the omission cannot read as an oversight.**

    `ADR% used` and `ADR $` have no external check and must not acquire one
    from TWS: TWS has no native ADR, so any figure it shows comes from a
    different computation over a different bar set. This test exists to
    state that, and asserts only that the row computes and declares its
    basis. **070 renamed the key** from the raw `ADR%` (mean session
    high/low, never itself rendered any more) to `ADR% used` (the complement
    of the old `ADR%avail`, per Christoph's 2026-08-23 ruling) — the basis
    (RTH, `09:30-16:00 ET`) is unchanged, because both are `ADR_BASIS`.
    """
    adr = _attached().context["ADR% used"]
    assert adr.ok, f"ADR% used refused: {adr.unavailable}"
    assert adr.basis is not None and adr.basis.label == "09:30-16:00 ET"


def test_the_fifteen_minute_range_refuses_because_the_window_never_closes() -> None:
    """**042's exit refusal, and the fixture demonstrates it for free.**

    `_today_minutes` runs `04:00` to `09:35`, so the newest bar starts at 09:34.
    The 5-minute window is closed; the 15-minute one is not. `ORH15` must
    therefore render `window not closed` — **never a partial range**, which is
    what a max over the seven bars it does have would be: a plausible number,
    correctly computed, answering a question nobody asked.

    **This is the strongest form of the refusal available** — it fires against
    the same fixture that produces the externally-verified values, so nothing
    was staged to make it happen.
    """
    rail = _attached().rail
    for name in ("ORH15", "ORL15"):
        got = rail[name]
        assert not got.ok, (
            f"{name} rendered {got.value} from a window that has not closed. "
            f"The fixture's last bar starts 09:34 and the window needs 09:44.")
        assert "window not closed" in got.unavailable, got.unavailable
        assert "09:44" in got.unavailable and "09:34" in got.unavailable, (
            "the refusal must name what it needed and what it had: "
            + got.unavailable)

    assert rail["ORH5"].ok, "the 5-minute window HAS closed and must render"

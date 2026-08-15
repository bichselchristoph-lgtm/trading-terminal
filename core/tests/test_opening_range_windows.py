"""`042` Part 1 — two opening-range windows, containment, and the refusal.

**The containment property is why two windows are safe to carry side by side.**
`ORH15 >= ORH5` and `ORL15 <= ORL5`, always, because 09:30–09:45 contains
09:30–09:35. If it ever failed, the two rows would be measuring different things
under names that claim otherwise — which is `042`'s whole reason for splitting a
bare `ORH` in the first place.

**The fixture in `live/tests/test_qqq_2026_08_13_regression.py` cannot check
this**, and that is worth stating rather than discovering. It runs to 09:35, so
its 15-minute window never closes and `ORH15` correctly refuses. Even if it did
close, both extremes sit in the 09:30 bar, so the property would hold only as
equality — true, and no evidence at all that the windows are being sliced
differently. **These bars are built so the two windows genuinely disagree.**
"""
from __future__ import annotations

from core.indicators.context import Bar, Measured, level_rail


def bar(clock: str, hi: float, lo: float) -> Bar:
    return Bar(ts=f"2026-08-13T{clock}:00", open=lo, high=hi, low=lo,
               close=hi, volume=1000, wap=(hi + lo) / 2)


#: 09:30–09:45, one bar a minute. **The extremes are OUTSIDE the first five
#: minutes on purpose** — 09:40 makes the high and 09:42 the low — so a rail
#: that sliced both windows the same way would be caught.
SIXTEEN = (
    [bar(f"09:{30 + i}", 100.0 + i * 0.01, 99.0 - i * 0.01) for i in range(5)]
    + [bar("09:35", 100.20, 99.80), bar("09:36", 100.30, 99.70),
       bar("09:37", 100.40, 99.60), bar("09:38", 100.50, 99.50),
       bar("09:39", 100.60, 99.40), bar("09:40", 101.50, 99.30),
       bar("09:41", 100.80, 99.20), bar("09:42", 100.90, 98.10),
       bar("09:43", 101.00, 99.00), bar("09:44", 101.10, 98.90)]
)


def rail_at(clock: str) -> dict[str, Measured]:
    """The rail as it would render with the newest bar starting at `clock`."""
    upto = [b for b in SIXTEEN if b.ts[11:16] <= clock]
    return level_rail(
        prev_day=None,
        premarket=[],
        opening_5=[b for b in upto if "09:30" <= b.ts[11:16] < "09:35"],
        opening_15=[b for b in upto if "09:30" <= b.ts[11:16] < "09:45"],
        session_clock=clock,
        vwap=Measured.absent("not under test"),
        year_high=None, year_low=None, price=100.0,
        adr_dol=Measured.absent("not under test"),
    )


def test_the_fifteen_contains_the_five() -> None:
    """`042`: *note the composition property. Assert it if it is cheap.* It is."""
    rail = rail_at("09:44")
    assert rail["ORH5"].ok and rail["ORH15"].ok
    assert rail["ORH15"].value >= rail["ORH5"].value
    assert rail["ORL15"].value <= rail["ORL5"].value


def test_and_the_two_windows_actually_differ_here() -> None:
    """**Containment holds trivially when both windows see the same extreme.**

    A test that only asserted `>=` would pass against a rail that sliced both
    windows identically — the containment would be equality and nothing would
    say so. These bars put the high at 09:40 and the low at 09:42, so the two
    rows must disagree.
    """
    rail = rail_at("09:44")
    assert rail["ORH15"].value == 101.50 and rail["ORH5"].value == 100.04
    assert rail["ORL15"].value == 98.10 and rail["ORL5"].value == 98.96
    assert rail["ORH15"].value > rail["ORH5"].value
    assert rail["ORL15"].value < rail["ORL5"].value


def test_each_window_names_its_own_hours() -> None:
    """The window is part of the name and it renders. Two rows whose samples
    read alike are two rows a reader will treat as one."""
    rail = rail_at("09:44")
    assert "09:30-09:35 ET" in rail["ORH5"].sample
    assert "09:30-09:45 ET" in rail["ORH15"].sample


# ---- the refusal -----------------------------------------------------------

def test_before_0934_neither_window_has_closed() -> None:
    rail = rail_at("09:33")
    for name in ("ORH5", "ORL5", "ORH15", "ORL15"):
        assert not rail[name].ok, f"{name} rendered a partial range at 09:33"
        assert "window not closed" in rail[name].unavailable


def test_at_0934_the_five_closes_and_the_fifteen_does_not() -> None:
    """**The case the refusal exists for.** Both rows have bars; only one has a
    complete window. Rendering `ORH15` here would be a 5-minute range wearing a
    15-minute name — correctly computed, plausible, and wrong."""
    rail = rail_at("09:34")
    assert rail["ORH5"].ok, "09:34 starts the last bar of 09:30-09:35"
    assert not rail["ORH15"].ok
    assert "09:44" in rail["ORH15"].unavailable, (
        "the refusal must name the minute it is waiting for: "
        + rail["ORH15"].unavailable)


def test_at_0944_both_close() -> None:
    rail = rail_at("09:44")
    assert rail["ORH5"].ok and rail["ORH15"].ok


def test_no_session_clock_refuses_rather_than_assuming_the_window_closed() -> None:
    """Pre-open, or a symbol with no session bars at all. **The absence of a
    clock is not evidence that the window closed** — defaulting the other way
    would render a range for a session that has not started."""
    rail = level_rail(
        prev_day=None, premarket=[], opening_5=[], opening_15=[],
        session_clock=None,
        vwap=Measured.absent("x"), year_high=None, year_low=None,
        price=100.0, adr_dol=Measured.absent("x"))
    for name in ("ORH5", "ORL5", "ORH15", "ORL15"):
        assert not rail[name].ok
        assert "window not closed" in rail[name].unavailable


def test_a_bare_orh_or_orl_does_not_exist() -> None:
    """`042`: *a bare `ORH` must not survive anywhere.* It is a well-formed name
    answering two different questions, which is this project's defining defect."""
    rail = rail_at("09:44")
    assert "ORH" not in rail and "ORL" not in rail

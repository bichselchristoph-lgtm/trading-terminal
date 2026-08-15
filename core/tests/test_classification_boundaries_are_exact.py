"""044 Part 2 — a classification boundary is not evaluated in floating point.

**`OBS-054`. The design session's defect, and it costs a limit.** `039` specified
the bands closed at `±0.05R` and `+1.0R` and never said what arithmetic the
comparison happens in. In binary floating point a trade exactly on an edge
usually is not::

    (9.95 - 10.0) / 1.0  ==  -0.050000000000000710

**A trade that made nothing and lost nothing classifies as `L`** — the only class
feeding `losses_max_day` and both R-lost caps. **A limit firing on a rounding
error, indistinguishable on screen from a bad day.**

----

**Every case here is CONSTRUCTED FROM PRICES, never from a literal `R_closed`.**

044 is explicit about why, and it is the reason the original defect survived a
suite of 35 tests: *a test that hands the classifier a Decimal it already
rounded tests nothing — it must go through the same arithmetic the real path
does.* A test that builds `Decimal("-0.05")` and asks what class it is proves
only that comparison operators work. The defect lives in the **division**, so the
division has to happen inside the test's subject.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.risk.classify import (ClosedTrade, R_PLACES, TradeClass, classify,
                                r_closed)

#: 100 shares long at $10.00 with the stop at $9.00. **1R is exactly $1.00 per
#: share**, so an exit price maps to an R value a reader can check by eye:
#: $9.95 is −0.05R, $11.00 is +1.00R. The whole point is that the numbers are
#: obvious and the arithmetic is not.
FILL, STOP, QTY = 10.0, 9.0, 100


def at_exit(price: float, commissions: float = 0.0) -> ClosedTrade:
    return ClosedTrade(avg_fill=FILL, avg_exit=price, quantity=QTY,
                       commissions=commissions, stop_at_entry=STOP)


# ---- 044's five cases ------------------------------------------------------


@pytest.mark.parametrize("exit_price,expected_r,expected_class", [
    # **The two that used to misfile, and the lower one is the expensive one.**
    ("9.95",  "-0.0500", TradeClass.BREAK_EVEN),
    ("10.05", "0.0500",  TradeClass.BREAK_EVEN),
    # **The upper band, where a genuine winner used to land as a Partial.**
    ("11.00", "1.0000",  TradeClass.WINNER),
    ("10.9999", "0.9999", TradeClass.PARTIAL),
    # **One tick outside, which must still be a loss.** A fix that swallowed
    # this would have replaced a false `L` with a false `BE`, which is worse:
    # the first over-counts a limit and the second hides one.
    ("9.9499", "-0.0501", TradeClass.LOSER),
])
def test_a_boundary_classifies_on_the_exact_value(
        exit_price: str, expected_r: str, expected_class: TradeClass) -> None:
    trade = at_exit(float(exit_price))
    r = r_closed(trade)

    assert r == Decimal(expected_r), (
        f"exit {exit_price} gave R_closed={r}, expected exactly "
        f"{expected_r}. The division is where the float artefact lived.")
    assert classify(trade).trade_class is expected_class, (
        f"R_closed={r} classified as {classify(trade).trade_class}, "
        f"expected {expected_class}.")


def test_the_stored_and_the_classified_r_are_the_same_number() -> None:
    """**044: a record reading `−0.0500` beside a class of `L` must never
    coexist.**

    This is what the previous `_EDGE = 1e-9` fix could not give. Widening every
    comparison by a tolerance made the *class* right while leaving the *stored*
    value as the raw float — so the record and its label disagreed, and the
    record is what any later question about cutting winners short will be
    answered from.
    """
    for price in ("9.95", "10.05", "11.00", "9.9499", "10.9999"):
        result = classify(at_exit(float(price)))
        assert result.r_closed == r_closed(at_exit(float(price)))
        assert result.r_closed == result.r_closed.quantize(R_PLACES), (
            f"{price}: the stored R_closed is not quantised — "
            f"{result.r_closed}")


def test_the_float_path_really_did_misclassify(  ) -> None:
    """**The defect, reproduced in the open, so the fix is not taken on faith.**

    Not a test of our code — a test of the arithmetic 044 cites. If this ever
    stops being true, floating point has changed and the rest of this file needs
    rereading rather than trusting.
    """
    naive = (9.95 - 10.0) / (10.0 - 9.0)
    assert naive < -0.05, (
        "the float subtraction no longer escapes the band; 044's premise has "
        "changed")
    assert str(naive).startswith("-0.05000000000000"), str(naive)

    # And the same inputs through the real path land exactly on the edge.
    assert r_closed(at_exit(9.95)) == Decimal("-0.0500")


def test_commissions_do_not_reintroduce_the_float() -> None:
    """The commission is subtracted inside the same `Decimal` expression.

    A fix that quantised only the quotient would let a float commission put the
    numerator back into binary before the division — the artefact would return
    by a different door, and only on trades that cost money to make.
    """
    # $5 of commission on $100 of risk is exactly -0.05R of drag.
    trade = at_exit(10.05, commissions=10.0)
    assert r_closed(trade) == Decimal("-0.0500")
    assert classify(trade).trade_class is TradeClass.BREAK_EVEN


def test_a_short_lands_on_the_edge_too() -> None:
    """**The absolute value on the denominator must not round differently.**

    Short 100 @ $10.00, stop $11.00, covered at $10.05 — the mirror of the long
    scratch, and it must classify identically. A sign handled outside the
    `Decimal` expression is how one side gets a tolerance the other does not.
    """
    short = ClosedTrade(avg_fill=10.0, avg_exit=10.05, quantity=-100,
                        stop_at_entry=11.0)
    assert r_closed(short) == Decimal("-0.0500")
    assert classify(short).trade_class is TradeClass.BREAK_EVEN

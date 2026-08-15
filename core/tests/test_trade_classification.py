"""`039` Part 2 — the four classes, the sum, and the refusal.

**The refusal is the test that matters most.** A trade with no `stop_at_entry`
must classify as `unavailable (no entry stop recorded)` and **never as break
even** — break even is the class that counts against no limit, so defaulting to
it turns a missing field into a silently free trade.

**The sum test is the one that would otherwise sit red for weeks.** `trades =
W + P + L + BE` is the kind of invariant everybody assumes and nobody checks;
`039` asks for it explicitly and asks that it be seen red by miscounting one
class deliberately, which `test_the_sum_can_actually_fail` does.
"""
from __future__ import annotations

import pytest

from core.risk.classify import (
    COMMISSION_BASIS,
    DEFAULT_THRESHOLDS,
    Classified,
    ClassificationThresholds,
    ClosedTrade,
    Counters,
    TradeClass,
    classify,
    r_closed,
    r_lost,
    r_net,
    tally,
)


def long_trade(exit_price: float, *, commissions: float = 0.0,
               stop: float | None = 9.0) -> ClosedTrade:
    """100 shares long at $10 with a $9 stop — 1R is exactly $1.00/share."""
    return ClosedTrade(avg_fill=10.0, avg_exit=exit_price, quantity=100,
                       commissions=commissions, stop_at_entry=stop)


# ---- the four classes ------------------------------------------------------

@pytest.mark.parametrize(
    "exit_price, expected",
    [
        (11.00, TradeClass.WINNER),      # exactly +1.00R — the boundary is inclusive
        (12.50, TradeClass.WINNER),
        (10.60, TradeClass.PARTIAL),     # +0.60R — the value the record exists to keep
        (10.06, TradeClass.PARTIAL),     # just outside the band
        (10.05, TradeClass.BREAK_EVEN),  # exactly +0.05R — inclusive
        (10.00, TradeClass.BREAK_EVEN),
        (9.95, TradeClass.BREAK_EVEN),   # exactly -0.05R — inclusive
        (9.94, TradeClass.LOSER),        # just outside
        (9.00, TradeClass.LOSER),        # -1.00R, the full stop
    ],
)
def test_each_class_at_and_around_its_boundary(exit_price: float,
                                               expected: TradeClass) -> None:
    assert classify(long_trade(exit_price)).trade_class is expected


def test_the_boundaries_are_the_stated_ones_and_leave_no_gap() -> None:
    """Every R lands in exactly one class. A gap between `P` and `BE` would make
    some trades unclassifiable for a reason nobody wrote down."""
    for step in range(-300, 301):
        r = step / 100.0
        result = classify(long_trade(10.0 + r))
        assert result.trade_class is not None, f"R={r} classified as nothing"


def test_an_exact_edge_scratch_is_not_a_loser() -> None:
    """**The boundary defect, pinned. This one costs a limit.**

    `$10.00` fill, `$9.00` stop, exit `$9.95` is exactly `-0.05R` and `039`
    puts it inside the break-even band. In binary floating point the subtraction
    yields `-0.050000000000000710`, which is outside it — so the naive
    comparison classifies a scratch as `L`, and `L` is the only class that feeds
    `losses_max_day`, `losses_max_month` and the R-lost caps.

    **A limit firing on a rounding error, on a trade that made no money and lost
    none.** Found by the parametrised boundary case above; kept separately
    because the parametrisation reads as coverage and this reads as the reason.
    """
    scratch = long_trade(9.95)
    assert r_closed(scratch) < -0.05          # the raw arithmetic IS outside the band
    assert classify(scratch).trade_class is TradeClass.BREAK_EVEN
    assert r_lost([classify(scratch)]) == 0.0
    assert tally([classify(scratch)]).losers == 0


# ---- direction -------------------------------------------------------------

def test_a_short_winner_is_a_winner_and_not_its_mirror_image() -> None:
    """Signed quantity carries the direction; there is no side branch.

    Short 100 @ $10 with the stop above at $11, covered at $9 — a full +1R. The
    absolute value on the denominator is what makes this work: without it the
    risk is negative and the short classifies as a `LOSER`.
    """
    short = ClosedTrade(avg_fill=10.0, avg_exit=9.0, quantity=-100,
                        stop_at_entry=11.0)
    result = classify(short)
    assert result.trade_class is TradeClass.WINNER
    assert result.r_closed == pytest.approx(1.0)


def test_a_short_loser_is_a_loser() -> None:
    short = ClosedTrade(avg_fill=10.0, avg_exit=11.0, quantity=-100,
                        stop_at_entry=11.0)
    assert classify(short).trade_class is TradeClass.LOSER


# ---- the frozen denominator ------------------------------------------------

def test_the_denominator_is_the_entry_stop_and_the_record_has_no_other() -> None:
    """`ClosedTrade` carries no live or trailing stop **at all**, which is how
    the wrong denominator is made unreachable rather than merely discouraged.
    Christoph moves stops up during a trade; a trailed winner divided by the
    live stop divides by nearly zero.
    """
    assert not hasattr(ClosedTrade(10.0, 11.0, 100), "stop_now")
    assert not hasattr(ClosedTrade(10.0, 11.0, 100), "trailing_stop")


# ---- commissions -----------------------------------------------------------

def test_commissions_move_a_gross_scratch_into_a_loss() -> None:
    """`039` Part 2's own example, in numbers: a $25 gross scratch that cost $2
    to trade is a small loss. Here a +0.05R gross scratch — exactly on the band
    edge — falls out of it once commissions are taken."""
    gross = long_trade(10.05)
    assert classify(gross).trade_class is TradeClass.BREAK_EVEN

    net = long_trade(10.05, commissions=2.0)
    assert classify(net).r_closed == pytest.approx(0.03)
    assert classify(net).trade_class is TradeClass.BREAK_EVEN  # 0.03R still inside

    heavier = long_trade(10.05, commissions=7.0)
    assert classify(heavier).r_closed == pytest.approx(-0.02)
    assert classify(heavier).trade_class is TradeClass.BREAK_EVEN

    heaviest = long_trade(10.05, commissions=12.0)
    assert classify(heaviest).r_closed == pytest.approx(-0.07)
    assert classify(heaviest).trade_class is TradeClass.LOSER


def test_the_commission_basis_is_declared_and_is_net() -> None:
    assert COMMISSION_BASIS == "net"


def test_zero_commission_reduces_to_the_formula_039_states() -> None:
    """`R_closed = (avg_exit - avg_fill) / (avg_fill - stop_at_entry)`.

    `039` states the per-share form and also requires classification net of
    commissions; the per-share form has nowhere to put one. The dollar form is
    implemented and this pins the two together at the point where they must
    agree.
    """
    for exit_price in (8.5, 9.7, 10.0, 10.4, 11.9):
        stated = (exit_price - 10.0) / (10.0 - 9.0)
        assert r_closed(long_trade(exit_price)) == pytest.approx(stated)


# ---- the refusal -----------------------------------------------------------

def test_a_trade_with_no_entry_stop_is_unavailable_and_never_break_even() -> None:
    """`039`'s refusal exit test, stated as its own case because the tempting
    default is the one class that counts against nothing."""
    result = classify(long_trade(10.0, stop=None))
    assert result.trade_class is None
    assert result.r_closed is None
    assert result.unavailable == "no entry stop recorded"
    assert result.is_available is False


def test_a_zero_risk_trade_is_also_unavailable_and_not_break_even() -> None:
    """Stop equal to fill. The denominator does not exist, so neither does the
    number — and `0/0` defaulting to break even is the same failure wearing a
    different hat."""
    result = classify(long_trade(10.0, stop=10.0))
    assert result.trade_class is None
    assert result.unavailable is not None


# ---- the counters ----------------------------------------------------------

def test_trades_equals_w_plus_p_plus_l_plus_be() -> None:
    """The invariant `039` Part 2 asks to be asserted."""
    results = [
        classify(long_trade(12.0)),   # W
        classify(long_trade(11.0)),   # W
        classify(long_trade(10.6)),   # P
        classify(long_trade(10.0)),   # BE
        classify(long_trade(9.0)),    # L
    ]
    counters = tally(results)
    assert counters.trades == 5
    assert (counters.winners, counters.partials,
            counters.break_evens, counters.losers) == (2, 1, 1, 1)
    assert counters.trades == (counters.winners + counters.partials
                               + counters.break_evens + counters.losers)


def test_the_sum_can_actually_fail() -> None:
    """Seen red by miscounting one class deliberately.

    A test that cannot fail proves nothing, and the whole value of the sum is
    that it catches a counter set drifting apart.
    """
    with pytest.raises(ValueError, match="counters do not sum"):
        Counters(trades=5, winners=2, partials=1, break_evens=1, losers=0,
                 unclassifiable=0)


def test_an_unclassifiable_trade_is_counted_and_is_outside_trades() -> None:
    """**This is a hole, and the test exists to make it visible rather than to
    bless it.**

    `039` Part 2 says all four classes count toward `trades`, and Part 3 makes
    `trades_max_day` a limit. A closed trade with no `stop_at_entry` therefore
    counts toward **no limit at all**. The invariant is implemented exactly as
    `039` asks; `closed_total` is the number that does include it, nothing reads
    `closed_total` today, and the consequence is recorded in the ledger.
    """
    results = [classify(long_trade(11.0)), classify(long_trade(10.0, stop=None))]
    counters = tally(results)
    assert counters.trades == 1
    assert counters.unclassifiable == 1
    assert counters.closed_total == 2


# ---- losses accumulate, gains buy no room ----------------------------------

def test_r_lost_ignores_gains_entirely() -> None:
    """`039` Part 3: *a +10R swing closing today must not buy back two losing
    trades and defer the cap.*"""
    results = [
        classify(long_trade(20.0)),   # +10R
        classify(long_trade(9.0)),    # -1R
        classify(long_trade(9.5)),    # -0.5R
    ]
    assert r_lost(results) == pytest.approx(-1.5)
    assert r_net(results) == pytest.approx(8.5)


def test_a_scratch_inside_the_band_is_not_an_r_loss() -> None:
    assert r_lost([classify(long_trade(9.97))]) == 0.0


def test_r_net_is_information_and_r_lost_is_the_limit() -> None:
    """They must not be the same number on a mixed day, or one row on the panel
    is telling you nothing the other did not."""
    results = [classify(long_trade(12.0)), classify(long_trade(9.0))]
    assert r_lost(results) != r_net(results)


# ---- the thresholds --------------------------------------------------------

def test_the_defaults_are_unfitted_and_say_where_they_came_from() -> None:
    assert DEFAULT_THRESHOLDS.fitted is False
    assert "2026-08-14" in DEFAULT_THRESHOLDS.source
    assert DEFAULT_THRESHOLDS.breakeven_band_r == 0.05
    assert DEFAULT_THRESHOLDS.winner_min_r == 1.00


def test_overlapping_bands_are_refused_at_construction() -> None:
    """A band wider than the winner floor makes `PARTIAL` unreachable — and the
    counters would still sum, so nothing downstream would notice."""
    with pytest.raises(ValueError, match="do not order"):
        ClassificationThresholds(breakeven_band_r=1.5, winner_min_r=1.0,
                                 source="test")


def test_the_band_is_in_r_not_in_percent_of_price() -> None:
    """The regression `039` Part 2 names in full: 1% of a $733 entry is $7.33 a
    share, which on 480 shares is $3,518 — seven times 1R — classified as break
    even. The band being in R makes the instrument's price irrelevant.
    """
    cheap = ClosedTrade(avg_fill=4.00, avg_exit=4.02, quantity=100,
                        stop_at_entry=3.60)      # +0.05R
    dear = ClosedTrade(avg_fill=733.00, avg_exit=733.05, quantity=100,
                       stop_at_entry=732.00)     # +0.05R
    assert classify(cheap).trade_class is TradeClass.BREAK_EVEN
    assert classify(dear).trade_class is TradeClass.BREAK_EVEN
    assert classify(cheap).r_closed == pytest.approx(classify(dear).r_closed)

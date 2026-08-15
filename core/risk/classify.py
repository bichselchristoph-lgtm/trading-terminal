"""Closed-trade classification and the counters the limits read — `039` Parts 2 and 3.

**Pure. Nothing here fetches, writes, persists, or knows what a terminal is.**
A closed trade in, a class out. `core` imports nothing first-party, so this
module cannot reach `live.tui`'s grammar and returns its own types.

----

**Every closed trade is exactly one of four things**, and only one of them
counts against a limit:

    W   R_closed >= +1.00R                    counts toward: trades
    P   +0.05R < R_closed < +1.00R            counts toward: trades
    BE  -0.05R <= R_closed <= +0.05R          counts toward: trades
    L   R_closed < -0.05R                     counts toward: trades, losses

**`W`, `P` and `BE` exist as record fields, not as limits.** They are what makes
*am I cutting winners short?* answerable later — a month of `P` values clustered
near +0.6R says something specific, and folded into `W` it would be invisible.

----

**THE DENOMINATOR IS `stop_at_entry` AND IT IS FROZEN.** Christoph moves stops up
during a trade. Using the *live* stop makes a trailed winner divide by nearly
zero and makes a trailed loser read as a full -1R when a quarter was lost.
`stop_at_entry` is immutable on the trade record and is the only denominator
this module will accept. **Every later stop is management, not risk.**

**THE BAND IS IN R, NEVER IN PERCENT OF PRICE.** An earlier draft of `039` used
1% of entry price. On QQQ at $733 that is $7.33 per share -- on a 480-share
position, **$3,518, seven times 1R, classified as break even.** `0.05R` bounds
it at $25 whatever the instrument costs. This is the same reason `038` put the
anchored-window band in ADR rather than cents: a threshold in price units does
not transfer between a $4 name and a $700 one.

**CLASSIFICATION IS NET OF COMMISSIONS.** A $25 gross scratch that cost $2 to
trade is a small loss, not a break even. Gross-versus-net is an unstated basis,
which is this project's recurring defect.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TradeClass(Enum):
    """The four, and there is no fifth.

    The value is what renders and what is stored on the record -- `039` Part 5's
    `1W 1P 1L 0BE` row and Part 6's `class` field are the same vocabulary.
    """

    WINNER = "W"
    PARTIAL = "P"
    BREAK_EVEN = "BE"
    LOSER = "L"


#: `039` Part 2. **Net, and the alternative is not implemented rather than
#: merely not chosen.** A `gross` mode would be a second basis for the same
#: number, and two bases for one number with nothing on screen saying which is
#: the defect `038` spent a whole slice removing. `config/risk.yaml` declares
#: the key so the basis is visible where the thresholds are; it does not offer a
#: choice, and `tests/test_risk_config_matches_core.py` pins the two together.
COMMISSION_BASIS = "net"

#: **A boundary tolerance, and it is a limit-correctness fix rather than
#: tidiness.** `039` states the bands closed at their edges -- `BE` is
#: `-0.05R <= R <= +0.05R`. In binary floating point a trade that is exactly on
#: an edge usually is not: a $10.00 fill exiting at $10.05 against a $9.00 stop
#: gives `0.05000000000000071`, which is greater than `0.05`.
#:
#: **At the upper edge that misfiles a scratch as a Partial, and neither counts
#: against anything. At the LOWER edge it misfiles a scratch as a LOSER** --
#: and `L` is the one class that feeds `losses_max_day`, `losses_max_month` and
#: the R-lost caps. Untreated, this is a limit firing on a rounding error, on a
#: trade that made no money and lost none.
#:
#: Found by `test_each_class_at_and_around_its_boundary`, which is why the
#: parametrisation names the exact edges rather than only values either side of
#: them. Comparisons are widened by `_EDGE` so that an on-the-edge value always
#: lands in the *more conservative* class: `BE` rather than `L`, `W` rather
#: than `P`.
#:
#: 1e-9 is far below any real R -- 1R is hundreds of dollars, so a nanoR is a
#: fraction of a cent -- and far above the ~1e-16 relative error of the
#: arithmetic that produces it.
_EDGE = 1e-9


@dataclass(frozen=True)
class ClassificationThresholds:
    """A named, versioned parameter set carrying its source string.

    **`fitted` is False and that is rendered, not hidden.** `039` Part 5: these
    *"no longer gate anything -- no limit depends on them -- so they are
    classification only. Ship the values, render them `unfitted`, and answer
    them from the record."* Tenet 6: thresholds do not transfer.

    They are in `config/` and not beside the definition, which is the opposite
    of what `038` ruled for a session basis -- **correctly, and the distinction
    is the one `038` drew.** A basis is a fact about what an indicator *is*; a
    band around zero is a choice somebody could sensibly make differently. This
    is a setting, so it lives where settings live.
    """

    breakeven_band_r: float
    winner_min_r: float
    source: str
    fitted: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.breakeven_band_r < self.winner_min_r:
            raise ValueError(
                f"thresholds do not order: breakeven_band_r={self.breakeven_band_r} "
                f"must be >= 0 and < winner_min_r={self.winner_min_r}. Overlapping "
                "bands would make one class unreachable and the counters would still sum."
            )


DEFAULT_THRESHOLDS = ClassificationThresholds(
    breakeven_band_r=0.05,
    winner_min_r=1.00,
    source="christoph_ruling_2026-08-14, via handoff/inbox/039 Part 2",
    fitted=False,
)


@dataclass(frozen=True)
class ClosedTrade:
    """One round trip. **A trade opens when the position leaves zero and closes
    when it returns to zero** -- `039` Part 3.

    **Partial exits are position changes that do not reach zero and are
    therefore not trades.** This needs no side logic and no short-versus-sell
    classification: `quantity` is signed, so the sign carries the direction and
    IBKR reports position quantity without the terminal interpreting it.

    `stop_at_entry` is `Optional` **so that its absence is representable.** A
    field that cannot be missing is a field whose absence gets defaulted, and
    `039`'s refusal test exists precisely because the tempting default is break
    even -- the class that counts against nothing.
    """

    avg_fill: float
    avg_exit: float
    quantity: int                      # signed: > 0 long, < 0 short
    commissions: float = 0.0           # always a cost, always >= 0
    stop_at_entry: Optional[float] = None


@dataclass(frozen=True)
class Classified:
    """The result. **Exactly one of `trade_class` and `unavailable` is set.**

    Not an exception, because an unclassifiable trade is a thing the record must
    carry and the panel must render -- `unavailable (no entry stop recorded)`,
    never a number and never a class.
    """

    r_closed: Optional[float]
    trade_class: Optional[TradeClass]
    unavailable: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self.unavailable is None


def r_closed(trade: ClosedTrade) -> Optional[float]:
    """R net of commissions, or `None` if the denominator does not exist.

    `039` Part 2 states the per-share form::

        R_closed = (avg_exit - avg_fill) / (avg_fill - stop_at_entry)

    **That form has nowhere to put a commission, and the same Part requires
    classification to be net of them.** Both cannot be literally true, so this
    computes the dollar form, which reduces to the stated one exactly when
    commissions are zero::

        net P&L = (avg_exit - avg_fill) * quantity - commissions
        risk    = |(avg_fill - stop_at_entry) * quantity|
        R       = net P&L / risk

    **Signed `quantity` makes it side-agnostic with no branch.** Long 100 @ $10,
    stop $9, exit $11: `1.00 * 100 / |1.00 * 100|` = +1R. Short -100 @ $10, stop
    $11, exit $9: `(-1.00 * -100) / |(-1.00) * -100|` = +1R. **The absolute value
    on the denominator is load-bearing** -- without it a short's risk is negative
    and every short classifies as its own mirror image.
    """
    if trade.stop_at_entry is None:
        return None
    risk = abs((trade.avg_fill - trade.stop_at_entry) * trade.quantity)
    if risk == 0:
        return None
    net = (trade.avg_exit - trade.avg_fill) * trade.quantity - trade.commissions
    return net / risk


def classify(
    trade: ClosedTrade,
    thresholds: ClassificationThresholds = DEFAULT_THRESHOLDS,
) -> Classified:
    """Classify one closed trade, or refuse to.

    **The refusal is the important half.** `039`'s exit test: a trade with no
    `stop_at_entry` classifies as `unavailable (no entry stop recorded)` --
    **never as break even.** Break even is the class that counts against nothing,
    so defaulting to it turns a missing field into a silently free trade.
    """
    if trade.stop_at_entry is None:
        return Classified(None, None, "no entry stop recorded")

    r = r_closed(trade)
    if r is None:
        # stop_at_entry == avg_fill, or a zero-quantity record. A zero-risk
        # trade is not a break even either -- the denominator does not exist, so
        # neither does the number, and the same refusal applies for the same
        # reason.
        return Classified(None, None, "entry stop equals fill — no risk to divide by")

    band = thresholds.breakeven_band_r
    if r >= thresholds.winner_min_r - _EDGE:
        return Classified(r, TradeClass.WINNER)
    if r > band + _EDGE:
        return Classified(r, TradeClass.PARTIAL)
    if r >= -band - _EDGE:
        return Classified(r, TradeClass.BREAK_EVEN)
    return Classified(r, TradeClass.LOSER)


@dataclass(frozen=True)
class Counters:
    """What the limits in `039` Part 3 read.

    **`trades == winners + partials + break_evens + losers`**, asserted by
    `tally` and by `core/tests/test_trade_classification.py`. A counter set that
    does not sum is a defect that would otherwise sit unnoticed for weeks.

    **`unclassifiable` is NOT in `trades`, and that is a hole rather than a
    decision.** `039` Part 2 says *"All four count toward `trades`"* and Part 3
    makes `trades_max_day` a limit -- so a closed trade with no `stop_at_entry`
    counts toward **no limit at all** and the day's cap can be exceeded by
    trading without a recorded entry stop. The invariant `039` asks for is
    implemented exactly as asked; the consequence is surfaced here, counted, and
    recorded as an observation rather than resolved by quietly redefining
    `trades`.
    """

    trades: int
    winners: int
    partials: int
    break_evens: int
    losers: int
    unclassifiable: int

    def __post_init__(self) -> None:
        total = self.winners + self.partials + self.break_evens + self.losers
        if self.trades != total:
            raise ValueError(
                f"counters do not sum: trades={self.trades} but "
                f"W{self.winners} + P{self.partials} + BE{self.break_evens} + "
                f"L{self.losers} = {total}"
            )

    @property
    def closed_total(self) -> int:
        """Every closed trade, classified or not. **Not what any limit reads
        today** -- see the note on `unclassifiable`."""
        return self.trades + self.unclassifiable


def tally(results: list[Classified]) -> Counters:
    """Count a day's or a month's classifications."""
    by = {c: 0 for c in TradeClass}
    unclassifiable = 0
    for res in results:
        if res.trade_class is None:
            unclassifiable += 1
        else:
            by[res.trade_class] += 1
    return Counters(
        trades=sum(by.values()),
        winners=by[TradeClass.WINNER],
        partials=by[TradeClass.PARTIAL],
        break_evens=by[TradeClass.BREAK_EVEN],
        losers=by[TradeClass.LOSER],
        unclassifiable=unclassifiable,
    )


def r_lost(results: list[Classified]) -> float:
    """The R that counts toward `r_max_loss_day` / `r_max_loss_month`.

    **LOSSES ONLY, NEVER NET, and this is the whole point of the function
    existing separately from a sum.** `039` Part 3: *a +10R swing closing today
    must not buy back two losing trades and defer the cap.* **Losses accumulate;
    gains buy no room.** Returned as a negative number, or 0.0 for a clean day.

    A trade is counted here if and only if it classified as `L`, so the
    break-even band governs this too: a -0.03R scratch is not a loss.
    """
    return sum(
        res.r_closed
        for res in results
        if res.trade_class is TradeClass.LOSER and res.r_closed is not None
    )


def r_net(results: list[Classified]) -> float:
    """Every classified trade summed. **Information only -- no limit reads it.**

    `039` Part 5 renders it with no ceiling, and the absence of a ceiling has to
    be visible rather than inferred: *a number with no ceiling on screen cannot
    tell you how close you are until it stops you*, so a row that has no limit
    must be distinguishable from one whose limit was forgotten.
    """
    return sum(res.r_closed for res in results if res.r_closed is not None)

"""058 Part 2 — the pacing guard, built rather than assumed.

IBKR's own documented limit: **six or more historical requests for the same
Contract, Exchange and Tick Type inside two seconds is a pacing violation.**
`OBS-079` found this in IBKR's own docs, not in either sibling repo this
project has, and 058's instruction is explicit: *build the guard, do not
rely on the arithmetic staying true.* A guard nobody has seen fail is
`B-035` again.

**Seen red first, by construction.** `test_six_requests_in_the_window_is_a_
violation` below fires the guard with exactly the fifth-and-sixth request
the task names — remove either of the last two calls in that test and it
passes for the wrong reason (headroom, not correctness); the assertion
that it MUST raise at six and MUST NOT raise at five is what keeps this
test able to fail rather than merely able to pass.
"""
from __future__ import annotations

import pytest

from live.attach.attach import Contract
from live.attach.ibkr import (PACING_LIMIT, PACING_WINDOW_S, IBKRMarketData,
                              _PacingGuard, _pacing_key)

QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="SMART",
              sector_etf="XLK")
NOSECTOR = Contract(symbol="THIN", con_id=1, exchange="SMART", sector_etf=None)


class RecordingManyIB:
    """A transport answering `reqHistoricalDataMany` — the seam `warm()`
    dispatches through. Records every batch it was asked to gather, in one
    call, so a test can assert on the SHAPE of the dispatch, not just the
    total count."""

    def __init__(self) -> None:
        self.batches: list[list[tuple]] = []

    def reqContractDetails(self, contract):
        return []

    def reqHistoricalDataMany(self, requests):
        self.batches.append(list(requests))
        return [[] for _ in requests]          # empty bars — shape, not values


# ---- the guard itself, isolated from any broker call -----------------------


def test_five_requests_in_the_window_is_fine() -> None:
    guard = _PacingGuard()
    key = ("QQQ", "SMART", "TRADES")
    guard.check(key, 5, now=100.0)          # must not raise


def test_six_requests_in_the_window_is_a_violation() -> None:
    """**The fifth-and-sixth request, watched fail.** One batch of six for
    one key inside the window must refuse — this is IBKR's own stated
    threshold, named in `OBS-079`."""
    guard = _PacingGuard()
    key = ("QQQ", "SMART", "TRADES")
    with pytest.raises(RuntimeError, match="pacing limit"):
        guard.check(key, 6, now=100.0)


def test_a_second_batch_inside_the_window_accumulates() -> None:
    """The limit is over the WINDOW, not per call. Four now and four a tenth
    of a second later is eight requests for one key inside two seconds —
    the exact shape a re-attach inside the cooldown would produce if the
    guard only looked at one batch at a time."""
    guard = _PacingGuard()
    key = ("QQQ", "SMART", "TRADES")
    guard.check(key, 4, now=100.0)
    with pytest.raises(RuntimeError, match="pacing limit"):
        guard.check(key, 4, now=100.1)


def test_the_window_expires() -> None:
    """A request outside the two-second window does not count against a new
    batch — the guard tracks a ROLLING window, not a running total."""
    guard = _PacingGuard()
    key = ("QQQ", "SMART", "TRADES")
    guard.check(key, 4, now=100.0)
    guard.check(key, 4, now=100.0 + PACING_WINDOW_S + 0.5)   # must not raise


def test_different_keys_do_not_share_a_budget() -> None:
    """**`OBS-079`'s caveat, named explicitly.** The sector ETF's requests
    are a DIFFERENT contract and must not count against the underlying's
    window — five of QQQ's plus five of XLK's is ten requests total and zero
    violations, because pacing is per `(contract, exchange, tickType)`."""
    guard = _PacingGuard()
    guard.check(("QQQ", "SMART", "TRADES"), 5, now=100.0)
    guard.check(("XLK", "SMART", "TRADES"), 5, now=100.0)     # must not raise


def test_pacing_key_is_symbol_exchange_tick_type() -> None:
    assert _pacing_key(QQQ) == ("QQQ", "SMART", "TRADES")


# ---- through `IBKRMarketData.warm()`, against a recording transport -------


def test_warm_dispatches_four_requests_for_a_symbol_with_no_sector() -> None:
    """058 Part 1 + Part 2, together: no sector mapping means no ETF
    requests, so the underlying's own four (the RTH/ETH daily pair, today,
    and the 20-session intraday) are what `warm()` gathers — well under the
    five-request ceiling, by construction rather than by stagger."""
    ib = RecordingManyIB()
    IBKRMarketData(ib).warm(NOSECTOR)
    assert len(ib.batches) == 1, "warm() must be ONE round trip, not several"
    assert len(ib.batches[0]) == 4, (
        f"expected 4 requests for a symbol with no sector, got "
        f"{len(ib.batches[0])}")


def test_warm_dispatches_six_requests_for_a_symbol_with_a_sector() -> None:
    """The sector ETF adds its own today + 20-session pair — two more
    requests, for a DIFFERENT contract, so it does not push the underlying's
    own pacing key anywhere near the limit."""
    ib = RecordingManyIB()
    IBKRMarketData(ib).warm(QQQ)
    assert len(ib.batches[0]) == 6, (
        f"expected 6 requests for a symbol with a sector mapping, got "
        f"{len(ib.batches[0])}")


def test_warm_refuses_a_re_attach_inside_the_pacing_window() -> None:
    """**The guard wired into `warm()` itself, not just the standalone
    class.** Warming the same symbol twice inside two seconds pushes its
    RTH/ETH/today/intraday group from four to eight requests — over the
    five-request ceiling — and `warm()` must refuse rather than dispatch a
    batch IBKR would flag as a violation."""
    ib = RecordingManyIB()
    md = IBKRMarketData(ib)
    md.warm(NOSECTOR)
    with pytest.raises(RuntimeError, match="pacing limit"):
        md.warm(NOSECTOR)

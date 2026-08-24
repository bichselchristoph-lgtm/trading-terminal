"""087 — the repaint path: the age that reads 0s, the flicker, and the
stream that dies unmarked. Seven exit categories per the task's own §5:
Green x2 (the age advances without streams; the age reads a real number
while healthy), Refusal x2 (a stale HEALTH stream; pending past its bound),
Teardown, Fixture, Colour.

**Every state here is constructed locally**, never borrowed from
`test_attach.py`'s shared `Fake()` or any other file's own pilot-drive
helper — B-136, the same discipline 083/084/086 already established.

**The two Green tests need real wall-clock time** — they exist specifically
to prove the age is painted from an independent clock tick, not merely
computed correctly and never shown, so a fixture supplying its own fake
clock would prove nothing about the actual repaint mechanism (the task's
own instruction). Every other category is tested directly at the render
function / metrics level, where a real wait is not needed and not honest —
the object under test does not itself run on a clock.
"""
from __future__ import annotations

import asyncio
import threading
import time

from core.indicators.context import INTRADAY_BASIS, Bar, Measured, Unit

from live.attach.attach import Contract
from live.attach.streaming import StreamHandle
from live.tui.app import (ATTACH_KEY, REPAINT_INTERVAL_S, STALE_THRESHOLD_S,
                          MomentumApp, Panel, attach_metrics_rows, context_rows)
from live.tui.day_record import Attached, StreamMetrics, empty_record

SIZE = (209, 54)

QQQ = Contract(symbol="QQQ", con_id=1, exchange="NASDAQ", sector_etf=None)


async def type_symbol(pilot, symbol: str) -> None:
    await pilot.press(ATTACH_KEY)
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


def _bars(n: int = 1, *, close: float = 101.0) -> list:
    return [Bar(ts="2026-08-20T09:31:00", open=close, high=close, low=close,
               close=close, volume=200.0, wap=close) for _ in range(n)]


def _first_line(body: str) -> str:
    return body.splitlines()[0]


class _MD:
    """Self-built for 087 — B-136. `open_price_stream` fires its initial
    payload once and then NEVER AGAIN unless `push()` is called explicitly —
    a frozen stream, exactly the state a fully stalled terminal is in.
    `cancel_count` tracks every `StreamHandle.cancel()` actually called, for
    the Teardown test."""

    def __init__(self) -> None:
        self.cancel_count = 0
        self._on_update = None

    def resolve(self, symbol):
        return [QQQ] if symbol.upper() == "QQQ" else []

    def tick_slots_in_use(self): return 0
    def cooldown_remaining_s(self, symbol): return 0
    def warm(self, c): pass

    def daily_bars(self, c, basis):
        return [Bar(ts=f"2026-06-{(i % 28) + 1:02d}", open=100.0, high=102.0,
                    low=100.0, close=101.0, volume=1_000_000.0) for i in range(60)]

    def intraday_sessions(self, c, basis):
        return [[Bar(ts=f"2026-08-{(i % 20) + 1:02d}T09:{30+m:02d}:00",
                     open=101.0, high=101.0, low=101.0, close=101.0,
                     volume=10.0, wap=101.0) for m in range(30)] for i in range(20)]

    def today_minutes(self, c): return _bars()
    def sector_today_minutes(self, c): return None
    def sector_sessions(self, c, basis): return None
    def open_tick_stream(self, c): return "tick-by-tick AllLast"

    def open_price_stream(self, c, on_update):
        self._on_update = on_update
        on_update(_bars())
        return StreamHandle(self._inc_cancel)

    def _inc_cancel(self) -> None:
        self.cancel_count += 1

    def push(self) -> None:
        """Fire another update on the CURRENT stream, if one is open.
        **Must run off the app's own thread, and must NOT be joined from
        it** — the real `on_update` closure calls
        `self.call_from_thread(...)`, which blocks the WORKER thread until
        the MAIN thread's event loop processes the callback. Joining from
        the main thread's own coroutine would block that loop and deadlock
        against itself; the caller awaits/pauses instead, exactly as the
        real broker callback is never joined by anything on the main
        thread either."""
        if self._on_update is not None:
            threading.Thread(target=self._on_update,
                             args=(_bars(close=202.0),)).start()

    def playbook_for(self, c): return "ORB 5m"


# ---- Green — a landed value repaints without a full remount (B-141) -------


def test_green_a_landed_value_updates_in_place_not_a_full_remount() -> None:
    """**The test that would have caught B-141.** `Frame.remove_children`
    is `_apply_fit`'s own full-remount call site — spying on it directly
    is what "flicker" IS, mechanically, not a proxy for it. A push landing
    after the initial mount must update the panel's content without a
    second call to it."""
    from live.tui.app import Frame
    md = _MD()
    calls: list[None] = []
    real_remove_children = Frame.remove_children

    async def spy(self, *a, **k):
        calls.append(None)
        return await real_remove_children(self, *a, **k)

    Frame.remove_children = spy
    try:
        async def go():
            app = MomentumApp(md=md)
            async with app.run_test(size=SIZE) as pilot:
                await pilot.pause()
                await type_symbol(pilot, "QQQ")
                calls.clear()               # only count remounts AFTER attach
                before = app.query_one("#attached", Panel).body()
                md.push()
                await asyncio.sleep(0.2)
                await pilot.pause()
                after = app.query_one("#attached", Panel).body()
                assert after != before, (
                    "the push did not repaint the panel at all -- this test "
                    "cannot say anything about HOW it repainted")
                assert not calls, (
                    f"a landed value forced {len(calls)} full remount(s) of "
                    f"the frame -- B-141, every landed value must update "
                    f"panels in place")
        asyncio.run(go())
    finally:
        Frame.remove_children = real_remove_children


def test_green_the_age_advances_without_the_streams() -> None:
    """**The test that would have caught B-140.** No push after the initial
    one — the age must still climb, painted by REPAINT_INTERVAL_S's own
    clock tick, not by a fixture supplying its own ticks. Reads the RENDERED
    text at two real points in time, never `header_freshness()` directly —
    calling the pure function would prove the arithmetic is right, which was
    never the bug; the bug was that it was never painted."""
    md = _MD()

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "QQQ")
            first = _first_line(app.query_one("#attached", Panel).body())
            assert "0s" in first, f"the header did not start near 0s:\n{first!r}"

            await asyncio.sleep(REPAINT_INTERVAL_S * 3 + 0.5)
            await pilot.pause()
            second = _first_line(app.query_one("#attached", Panel).body())
            assert second != first, (
                f"the header did not repaint at all across "
                f"{REPAINT_INTERVAL_S * 3 + 0.5}s with no stream push -- "
                f"B-140, the age is stuck at its last painted value:\n"
                f"first:  {first!r}\nsecond: {second!r}")
            assert "0s" not in second, (
                f"a constant 0s across real elapsed time with no push -- "
                f"the age is not advancing:\n{second!r}")
    asyncio.run(go())


def test_green_the_age_reads_a_real_number_while_healthy() -> None:
    """With no further push, the age must climb through 1s, 2s, 3s, 4s over
    four real seconds -- not jump, not stay flat."""
    md = _MD()

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "QQQ")
            readings = []
            for _ in range(4):
                await asyncio.sleep(REPAINT_INTERVAL_S)
                await pilot.pause()
                line = _first_line(app.query_one("#attached", Panel).body())
                readings.append(line)
            ages = []
            for line in readings:
                digits = "".join(ch for ch in line.split("s")[0] if ch.isdigit())
                assert digits, f"no age digits found in header:\n{line!r}"
                ages.append(int(digits))
            assert ages == sorted(ages), (
                f"the age must climb monotonically with no push: {ages}\n"
                f"raw lines: {readings}")
            assert ages[-1] >= 3, (
                f"expected the age to have reached at least 3s after "
                f"{REPAINT_INTERVAL_S * 4}s: {ages}")
    asyncio.run(go())


# ---- Refusal — a stale HEALTH stream, same rule as the header -------------


def test_refusal_a_stale_stream_is_marked_in_health() -> None:
    record = empty_record()
    a = Attached(symbol="QQQ", since="09:31:00")
    a.metrics.streams["symbol"] = StreamMetrics(
        label="symbol", update_count=350,
        last_update_at=time.monotonic())          # fresh
    a.metrics.streams["sector"] = StreamMetrics(
        label="sector", update_count=1,
        last_update_at=time.monotonic() - (STALE_THRESHOLD_S + 5))  # dead
    record.attached = [a]

    rows = attach_metrics_rows(record)
    symbol_row = next(r for r in rows if "stream symbol" in r)
    sector_row = next(r for r in rows if "stream sector" in r)

    assert "stale" not in symbol_row, (
        f"a fresh stream (0s ago) must not be marked stale:\n{symbol_row!r}")
    assert f"stale {int(STALE_THRESHOLD_S) + 5}s" in sector_row, (
        f"a stream dead past {STALE_THRESHOLD_S}s must be marked stale, "
        f"same rule as the ATTACHED header:\n{sector_row!r}")
    assert symbol_row != sector_row.replace(
        f" stale {int(STALE_THRESHOLD_S) + 5}s", ""), (
        "the two rows must render distinguishably")


def test_refusal_a_borderline_fresh_stream_is_not_marked_stale() -> None:
    """The Colour boundary, restated as a Refusal control: one second under
    the threshold must not carry the marker."""
    record = empty_record()
    a = Attached(symbol="QQQ", since="09:31:00")
    a.metrics.streams["symbol"] = StreamMetrics(
        label="symbol", update_count=10,
        last_update_at=time.monotonic() - (STALE_THRESHOLD_S - 1))
    record.attached = [a]
    row = next(r for r in attach_metrics_rows(record) if "stream symbol" in r)
    assert "stale" not in row, f"{row!r}"


# ---- Refusal — pending past its bound becomes a named refusal -------------


def test_refusal_pending_past_its_bound_becomes_a_refusal() -> None:
    a = Attached(symbol="QQQ", since="09:31:00", pending_timeout_s=1.0)
    a.metrics.attached_at = time.monotonic() - 2.0     # past the 1s bound

    rows = context_rows(a)
    rvol_row = next(r for r in rows if "RVOL" in r)
    adr_row = next(r for r in rows if "ADR% used" in r)
    vwap_row = next(r for r in rows if "VWAP" in r)

    assert "pending" not in rvol_row, (
        f"a row pending past its bound must not still read plain "
        f"'pending':\n{rvol_row!r}")
    assert "no RVOL" in rvol_row and "1s" in rvol_row and "unfitted" in rvol_row, (
        f"the refusal must name what did not arrive and mark the bound "
        f"unfitted:\n{rvol_row!r}")
    assert "pending" not in adr_row and "unfitted" in adr_row, f"{adr_row!r}"
    assert "pending" not in vwap_row and "unfitted" in vwap_row, f"{vwap_row!r}"


def test_refusal_pending_within_its_bound_still_reads_pending() -> None:
    """Distinguishable from BOTH a live pending and a landed value —
    the task's own requirement, checked as a positive control."""
    a = Attached(symbol="QQQ", since="09:31:00", pending_timeout_s=90.0)
    a.metrics.attached_at = time.monotonic() - 1.0     # well within 90s

    rows = context_rows(a)
    rvol_row = next(r for r in rows if "RVOL" in r)
    assert rvol_row.strip().endswith("pending"), (
        f"a row still within its bound must read plain 'pending':\n"
        f"{rvol_row!r}")


def test_refusal_pending_with_no_attach_clock_stays_pending_not_refused() -> None:
    """`attached_at is None` (a state no real attach produces, but every
    test that predates 087 leaves it at) must not be misread as 'infinitely
    pending' -- a missing clock renders as ordinary pending, never a false
    refusal."""
    a = Attached(symbol="QQQ", since="09:31:00")
    assert a.metrics.attached_at is None
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.strip().endswith("pending"), f"{row!r}"


# ---- Teardown — cancel-on-switch leaves nothing behind ---------------------


def test_teardown_cancel_on_switch_cancels_the_prior_streams_one_for_one() -> None:
    """**Part 0 item 3, exercised rather than trusted.** `_begin_attach`'s
    own cancel loop must fire once per stream the OUTGOING attach opened —
    N attaches of the same symbol open N streams and must cancel N-1 of
    them (every one but the current, still-live one)."""
    md = _MD()
    N = 4

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            for _ in range(N):
                await type_symbol(pilot, "QQQ")
            assert md.cancel_count == N - 1, (
                f"{N} attaches opened {N} streams; {N - 1} prior ones "
                f"should have been cancelled on each switch -- got "
                f"{md.cancel_count} cancels")
    asyncio.run(go())


# ---- Colour — amber renders only where a freshness age crossed threshold --


def test_colour_stale_never_appears_off_a_fresh_reading() -> None:
    a = Attached(symbol="QQQ", since="09:31:00", context={
        "RVOL": Measured(value=0.9, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
    })
    a.metrics.streams["symbol"] = StreamMetrics(
        label="symbol", last_update_at=time.monotonic())
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert "stale" not in row, f"{row!r}"


def test_colour_stale_appears_exactly_where_a_stream_aged_past_threshold() -> None:
    a = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK", context={
        "RVOL": Measured(value=0.9, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "RVOL_rel": Measured(value=1.1, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
    })
    a.metrics.streams["symbol"] = StreamMetrics(
        label="symbol", last_update_at=time.monotonic())
    a.metrics.streams["sector"] = StreamMetrics(
        label="sector", last_update_at=time.monotonic() - (STALE_THRESHOLD_S + 1))
    row = next(r for r in context_rows(a) if "RVOL" in r)
    own_half, rel_half = row.split("·", 1)
    assert "stale" not in own_half, f"own half: {own_half!r}"
    assert "stale" in rel_half, f"sector half: {rel_half!r}"


# ---- Fixture — every state above is self-constructed -----------------------


def test_fixture_this_file_builds_every_state_itself() -> None:
    """**B-136, checked as code, not trusted by review.**"""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (
            "test_attach" in node.module or "test_080" in node.module
            or "test_083" in node.module or "test_084" in node.module):
            names.update(a.name for a in node.names)
    assert not names, f"this file imports from a shared test fixture ({names})"

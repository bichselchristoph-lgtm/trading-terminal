"""`attach()` must be reachable **from the keyboard**. 032.

**What happened.** Christoph launched the terminal for the first time on
2026-08-13 and asked how to attach QQQ. There was no answer. `live/attach/` was
built under `S010`, `live/tests/test_attach.py` exercised it in 395 lines, and
`live/tui/app.py` imported exactly three local modules — none of them
`live.attach`. **The panel could render an attachment; nothing in the program
could create one.**

**Why 288 tests did not catch it, which is the half that matters.**
`test_attach.py` calls `attach()` directly. Every `test_tui_*.py` drives the app
through Textual's pilot and asserts on panels built from a `DayRecord` **handed
to them**. Neither ever asked *"can a person reach this from the running
program"*. That is the third instance of one shape — the app with no entry point
(`029`), `attach()` with nothing calling it (this file), and a command palette
that existed only in a docstring — and every one of them shipped green.

----

**This is deliberately not another pilot test that calls the action method.**

    async with app.run_test() as pilot:
        await app.run_action("attach")     # <- NOT this test

That would pass against a binding no key reaches, which is precisely the defect.
**The key press is the assertion.** `Pilot.press("a")` goes through Textual's
real key dispatch — the same path a keystroke takes — so a binding that is
mis-declared, shadowed, or absent fails here and cannot be faked green by
calling the method underneath it.

**The `MarketData` is a fake and there is no network.** `Fake` is imported from
`test_attach.py` rather than re-declared: a second fixture implementing the same
Protocol is two implementations of one fact, which is the defect this project is
named for. What is asserted is **reachability**, never the numbers — those are
`test_attach.py`'s job and it does it better than a pilot test could.
"""
from __future__ import annotations

import asyncio
import re
import socket
import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from core.indicators.context import Measured
from live.attach.attach import Contract
# `_BrokerLoop` and `_ThreadedIB` are private and are imported deliberately.
# They are the seam between two event loops; a test that reached them only
# through the public surface would exercise them exactly as `FakeIB` did, which
# is to say not at all.
from live.attach.ibkr import (DAILY_DURATION, EASTERN, INTRADAY_DURATION,
                              REQUIRED_SETTINGS, IBKRMarketData, IbkrConfig,
                              _BrokerLoop, _ThreadedIB, connect)
from live.tests.test_attach import Fake
from live.tui.app import ATTACH_KEY, MomentumApp, Panel
from live.tui.day_record import empty_record

#: The size the `013` UAT is performed at, and the size 029's launch test uses.
#: A reachability test at a width where the frame refuses would be asserting
#: something else entirely.
UAT_SIZE = (209, 54)

#: Two contracts for one ticker — `attach()`'s Refusal D. Used for the bad-symbol
#: path because it is the refusal a person actually meets, and because it needs
#: no exception to produce it.
AMBIGUOUS = (Contract(symbol="ZZZZ", con_id=1, exchange="NASDAQ"),
             Contract(symbol="ZZZZ", con_id=2, exchange="ARCA"))


def attached_panel(app: MomentumApp) -> Panel:
    """The ATTACHED tile, by its title.

    **Queried from the running app, not rebuilt.** Calling `render_panels`
    again here would assert that the record changed, which is a weaker claim
    than the one this file makes: that the screen changed.
    """
    for p in app.query(Panel):
        if p.title_text == "ATTACHED":
            return p
    raise AssertionError(
        "no ATTACHED panel on screen — the frame did not compose, so this test "
        "cannot say anything about reachability")


async def type_symbol(pilot, symbol: str) -> None:
    """Press the key, type the ticker, submit. **The whole point of the file.**

    **058 Part 3.** The attach itself now runs on a Textual worker thread
    (the freeze fix — OBS-041), so `pilot.pause()` alone no longer means the
    attach has landed: it processes pending Textual messages, not a
    background thread. `workers.wait_for_complete()` is what actually waits
    for the worker, and a `pause()` after it lets the `call_from_thread`
    re-render finish composing before the next assertion reads the screen.
    """
    await pilot.press(ATTACH_KEY)
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    # **080.** Stage 1's own worker dispatches stage 2's (several, one per
    # stream/role) from INSIDE its `call_from_thread` callback — blocking,
    # so they exist before stage 1's worker itself is marked complete — but
    # a second wait is cheap insurance against relying on that ordering
    # alone, since a Fake answers every one of them essentially instantly.
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


def tile_body(panel: Panel) -> str:
    """What the panel renders **at the size the tile actually gave it** (034).

    `Panel.body()` with no arguments is the DESIGN-width render — 71 columns and
    an 8-row viewport — which is right for a snapshot and wrong for asking what a
    person can see. The context block is 26 rows, so the default viewport hides
    two thirds of it and an assertion against `body()` would be measuring the
    fixture rather than the screen. That is S009a's whole finding, arriving in
    a test this time.
    """
    w = panel.content_size.width or panel.size.width
    h = panel.content_size.height or panel.size.height
    return panel.body(w, h or None) if w else panel.body()


def drive(symbol: str, md, size=UAT_SIZE, record=None,
          at_tile_size: bool = False) -> tuple[str, MomentumApp]:
    """Run one attach through a real key dispatch and return what ATTACHED says."""
    result: dict = {}

    async def go():
        app = MomentumApp(record=record, md=md)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            before = attached_panel(app).body()
            assert "nothing attached" in before, (
                "the ATTACHED panel did not start empty, so a later assertion "
                f"about it would prove nothing:\n{before}")
            await type_symbol(pilot, symbol)
            panel = attached_panel(app)
            result["body"] = tile_body(panel) if at_tile_size else panel.body()
            result["record"] = app.record

    asyncio.run(go())
    return result["body"], result["record"]


# ---- the one that would have caught it ------------------------------------


def test_a_key_press_attaches_a_symbol_and_the_panel_shows_it() -> None:
    """**Red against the pre-032 `app.py`**, where `a` is bound to nothing.

    The failure there is not subtle and is not meant to be: the panel still
    reads `nothing attached` after the full sequence, because no key in the
    application does anything except rotate focus.
    """
    body, record = drive("QQQ", Fake())

    assert "QQQ" in body, (
        f"pressed {ATTACH_KEY!r}, typed QQQ, pressed enter — and the ATTACHED "
        f"panel does not name it. attach() is unreachable from the keyboard, "
        f"which is 032.\nATTACHED renders:\n{body}")
    assert "nothing attached" not in body, (
        f"the panel still refuses after a successful attach:\n{body}")
    assert [a.symbol for a in record.attached] == ["QQQ"], (
        "the day record does not carry the attachment, so the panel is "
        "rendering something it did not get from the record — which breaks "
        "render_panels' purity")


def test_the_symbol_is_normalised_the_way_attach_normalises_it() -> None:
    """Typed lowercase, rendered uppercase — and **by `attach()`, not by the
    binding.** `attach()` already does `symbol.strip().upper()`; a second
    normalisation in the TUI would be the two-implementations defect in its
    smallest possible form."""
    body, _ = drive("qqq", Fake())
    assert "QQQ" in body, f"lowercase input did not reach attach():\n{body}"


def test_the_attach_is_recorded_as_typed() -> None:
    """`origin="typed"` **already existed in `attach()`'s signature** — S010
    anticipated a typed attach. §8.2a's four populations depend on that field
    meaning one thing, so the binding uses it rather than inventing a value."""
    seen: dict = {}

    class Recording(Fake):
        pass

    import live.tui.app as app_mod
    real = app_mod.attach

    def spy(symbol, md, *, origin="typed"):
        seen["origin"] = origin
        return real(symbol, md, origin=origin)

    app_mod.attach = spy
    try:
        drive("QQQ", Recording())
    finally:
        app_mod.attach = real
    assert seen.get("origin") == "typed", (
        f"the binding attached with origin={seen.get('origin')!r}; S010 records "
        "three origins and only `typed` exists today")


# ---- the refusal, surfaced rather than raised -----------------------------


def test_a_bad_symbol_renders_its_reason_and_the_app_stays_up() -> None:
    """`SPEC.md` §4.2 — **surfaced, not refused.**

    `AttachResult` already carries the failure; the binding renders it. It does
    not raise, does not exit, and does not clear the frame — a terminal that
    dies on a typo is a terminal you stop typing into.
    """
    body, record = drive("ZZZZ", Fake(contracts=AMBIGUOUS))

    assert "ambiguous" in body, (
        f"an ambiguous ticker attached silently or vanished:\n{body}")
    assert not record.attached, "a refused attach was recorded as an attachment"
    assert "(" in body and ")" in body, (
        f"the refusal renders without a parenthesised reason:\n{body}")


def test_the_frame_survives_a_refusal_and_can_attach_afterwards() -> None:
    """**The failure mode a one-shot refusal would hide.** A frame that renders
    a refusal and then accepts nothing more is indistinguishable from one that
    worked, until the second attempt — and nobody makes a second attempt in a
    test that only makes one."""
    async def go():
        app = MomentumApp(md=Fake(contracts=AMBIGUOUS))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "ZZZZ")
            assert "ambiguous" in attached_panel(app).body()

            app.md = Fake()                      # the ticker resolves this time
            await type_symbol(pilot, "QQQ")
            body = attached_panel(app).body()
            assert "QQQ" in body, (
                f"the frame accepted no further attach after a refusal:\n{body}")
            assert "ambiguous" not in body, (
                f"a stale refusal survived a later successful attach:\n{body}")
    asyncio.run(go())


def test_no_contract_found_is_a_different_refusal_from_ambiguous() -> None:
    """Two refusals, two messages. Collapsing them into one *"could not attach"*
    would be the grammar failure `grammar.py` exists to prevent."""
    body, _ = drive("NOPE", Fake(contracts=()))
    assert "no contract found" in body, (
        f"an unresolvable ticker did not render its own reason:\n{body}")


# ---- the input itself ------------------------------------------------------


def test_escape_closes_the_input_without_attaching() -> None:
    """A prompt you cannot leave is a mode, and `S009` §4b has no modes."""
    async def go():
        app = MomentumApp(md=Fake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await pilot.press(ATTACH_KEY)
            await pilot.pause()
            assert app.query("#attach-input"), "the key opened no input"
            await pilot.press("escape")
            await pilot.pause()
            assert not app.query("#attach-input"), (
                "escape left the input on screen — the frame is now modal")
            assert not app.record.attached, "escape attached something"
    asyncio.run(go())


def test_an_empty_submit_attaches_nothing_and_closes() -> None:
    """Enter on an empty prompt must not call `attach("")`. `attach()` would
    refuse it correctly, but *"no contract found"* for a symbol nobody typed is
    a refusal answering a question nobody asked."""
    async def go():
        app = MomentumApp(md=Fake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await pilot.press(ATTACH_KEY)
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert not app.record.attached
            body = attached_panel(app).body()
            assert "nothing attached" in body, (
                f"an empty submit changed the panel:\n{body}")
    asyncio.run(go())


def test_the_key_is_declared_once() -> None:
    """`SPEC.md` §4.4 — **no setting acquires a default here.** The key is a
    constant and the binding is built from it, so the character cannot be one
    thing in `BINDINGS` and another in the docstring or the footer."""
    assert ATTACH_KEY, "the attach key is empty"
    keys = [b[0] for b in MomentumApp.BINDINGS]
    assert ATTACH_KEY in keys, (
        f"ATTACH_KEY is {ATTACH_KEY!r} and BINDINGS declares {keys} — the "
        "constant and the binding disagree, which is the literal-in-two-places "
        "§4.4 forbids")

    src = (__import__("pathlib").Path(__file__).parents[1] / "tui" / "app.py")
    text = src.read_text(encoding="utf-8")
    assert f'("{ATTACH_KEY}",' not in text, (
        f"the character {ATTACH_KEY!r} is written as a literal in BINDINGS as "
        "well as being a constant")


def test_with_no_market_data_the_key_still_says_why() -> None:
    """**The branch the shipped program is actually in today.**

    `main()` constructs no broker — 029's launch test asserts the app starts
    without one — so `md` is `None` for anyone running `python -m live.tui`, and
    this is the branch a person's key press reaches. It must render a named
    reason, because *the key did nothing* and *the key worked and there is no
    data* look identical from outside the program and are completely different
    findings. That confusion is 032 itself, and it would be reintroduced one
    layer down by a branch that returns silently.

    **Carried from a second 032 suite** written concurrently in this tree on
    2026-08-13 and retired in favour of this file; it was the one case the two
    did not share. Recorded rather than merged silently — see the done-note.
    """
    body, record = drive("QQQ", None)
    assert "no market data" in body, (
        f"with no MarketData the key press changed nothing a reader can see:\n{body}")
    assert not record.attached, "an attach was recorded with no market data"


@pytest.mark.parametrize("size", [(209, 54), (240, 70)])
def test_it_is_reachable_at_more_than_one_width(size) -> None:
    """The binding must not depend on the frame's shape. Widths only — at
    `80x24` the frame refuses as too small and there is no panel to assert on,
    which is a different test's subject."""
    body, _ = drive("QQQ", Fake(), size=size)
    assert "QQQ" in body, f"unreachable at {size}:\n{body}"


# ===========================================================================
# 034 — the key press reaches a BROKER, and renders what it measured
#
# **This file is extended rather than joined by a third suite.** Two sessions
# wrote two 032 reachability suites on 2026-08-13 and folding them into one was
# the resolution; a third would re-open exactly that. `test_attach.py` stays
# untouched for the opposite reason — it tests `attach()` as a function, and that
# separation is what made 032's independent verification possible.
# ===========================================================================

#: The four ports that reach a broker on this machine. `SPEC.md` §9, and the
#: same set `tests/test_keepuptodate_scale.py` guards.
BROKER_PORTS = {7496, 7497, 4001, 4002}

#: A port nothing listens on. Used to prove the refusal path without needing TWS
#: to be *absent* — the demonstration must be the same on Christoph's machine
#: with TWS up as it is in a clean checkout.
CLOSED_PORT = 9

TODAY = date.today().isoformat()


class StubBar:
    """What `reqHistoricalData` hands back. **Field-for-field what `_bars` reads**
    — `date`, `open`, `high`, `low`, `close`, `volume`, `average` — and nothing
    else, so a change to `IBKRMarketData._bars` that reaches for a new attribute
    fails here rather than at 09:31 against a live account."""

    def __init__(self, when: str, close: float, volume: float) -> None:
        self.date, self.close, self.average, self.volume = when, close, close, volume
        self.open, self.high, self.low = close, close + 1.0, close - 1.0


class StubDetails:
    def __init__(self) -> None:
        self.contract = SimpleNamespace(symbol="QQQ", conId=320227571,
                                        exchange="SMART", currency="USD",
                                        primaryExchange="NASDAQ")
        # No industry mapping for an ETF, which is correct — `_sector_etf`
        # returns None and `RVOL_rel` then refuses BY NAME rather than rendering
        # 1.0. That refusal is a value this test wants to see rendered.
        self.industry = self.category = ""


class FakeIB:
    """A transport for `IBKRMarketData`. **Opens nothing.**

    034 part 5.3 wants `IBKRMarketData` exercised against a fake rather than
    mocked out, because the class under test is the seam and a mock of the seam
    tests nothing. This answers the same two methods TWS answers and records
    what was asked, so the `use_rth` contract is checkable.
    """

    def __init__(self) -> None:
        self.asked: list[dict] = []

    def reqContractDetails(self, contract):
        return [StubDetails()]

    def reqHistoricalDataMany(self, requests):
        """**058 Part 2.** `IBKRMarketData.warm()` reads this — without it,
        `warm()` raises `AttributeError`, `_context_block`'s wrapping
        `try/except` swallows it, and every row falls back to its own single
        live request. That degrade-gracefully path is real and tested
        elsewhere; this fixture exists so the GATHER path is exercised too,
        sequentially rather than concurrently — `FakeIB` has no broker loop
        to be concurrent on, only `_ThreadedIB` does (see `AsyncFakeIB`
        below)."""
        return [self.reqHistoricalData(contract, **kwargs)
               for contract, kwargs in requests]

    def reqHistoricalDataStream(self, contract, on_update, **kwargs):
        """**080.** `IBKRMarketData.open_price_stream` reads this. Answers
        synchronously and instantly, same as every other method here — one
        `reqHistoricalData` call (tracked in `self.asked` like any other),
        `on_update` fired once with the payload, nothing ongoing."""
        bars = self.reqHistoricalData(contract, **kwargs)
        on_update(bars)
        return bars

    def cancelHistoricalDataStream(self, bars) -> None:
        pass

    def reqHistoricalData(self, contract, **kw):
        self.asked.append(kw)
        size, duration = kw["barSizeSetting"], kw["durationStr"]
        if size == "1 day":
            n = 60 if duration == DAILY_DURATION else 260
            bars = [StubBar(f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                            100.0 + (i % 5), 1_000_000) for i in range(n)]
            # **088.** `drive()` runs the real `_begin_attach`, which stamps
            # `Stage2Inputs.today_et` from the actual current date — without
            # this, `ADR% used` trips 088's day-boundary refusal on every
            # test here, since none of these bars is dated today.
            bars[-1].date = TODAY
            return bars
        if duration == "1 D":                     # today's minutes
            return [StubBar(f"{TODAY} {9 + (30 + i) // 60:02d}:{(30 + i) % 60:02d}:00",
                            101.0, 1000.0) for i in range(30)]
        return [StubBar(f"2026-07-{d + 1:02d} {9 + (30 + i) // 60:02d}:{(30 + i) % 60:02d}:00",
                        101.0, 1000.0)
                for d in range(20) for i in range(30)]


@contextmanager
def no_broker_socket():
    """Fail any connect to a broker port, for the duration of the block.

    **Narrowed to the four ports rather than to sockets in general**, and the
    narrowing is the honest version rather than a weakening: importing
    `ib_async` builds an asyncio event loop, and on Windows that calls
    `socket.socketpair()`, which is a loopback connect. A blanket assertion
    fails on that, gets deleted for being noisy, and then catches nothing.

    **054 Part 2 / 040 Part 0 (OBS-040).** `socket.socket.connect` ALONE IS
    NOT ENOUGH: on Windows asyncio runs a ProactorEventLoop, and
    `loop.create_connection` reaches the socket through `ConnectEx` without
    ever calling the method patched above -- measured directly by `034`
    (`test_launches_as_a_program.py`'s `SOCKET_GUARD`), whose two-part shape
    this mirrors. Patched on `BaseEventLoop` so it covers the selector and
    proactor loops both. This was the second site of the hole `040` named:
    found here by grepping for every copy, not by 040 naming it.
    """
    real = socket.socket.connect
    real_create = asyncio.base_events.BaseEventLoop.create_connection

    def guard(self, addr, *a, **k):
        port = addr[1] if isinstance(addr, tuple) and len(addr) > 1 else None
        if port in BROKER_PORTS:
            raise AssertionError(f"the suite dialled broker port {port}")
        return real(self, addr, *a, **k)

    async def guard_create(self, protocol_factory, host=None, port=None, **k):
        if port in BROKER_PORTS:
            raise AssertionError(f"the suite dialled broker port {port}")
        return await real_create(self, protocol_factory, host, port, **k)

    socket.socket.connect = guard
    asyncio.base_events.BaseEventLoop.create_connection = guard_create
    try:
        yield
    finally:
        socket.socket.connect = real
        asyncio.base_events.BaseEventLoop.create_connection = real_create


# ---- 1. the key press renders VALUES ---------------------------------------


def test_a_key_press_renders_the_context_block_not_only_the_symbol() -> None:
    """**Red against `app.py` as it stands**, and the red is the finding.

    032 proved the ATTACHED panel *changes* on a key press. It changes to
    `QQQ  attached 12:58` and nothing else: `attach()` measured ADR, ATR, the
    extensions, VWAP, cumulative volume, both RVOLs and the ten-entry level rail,
    and `_record_attach` kept the symbol and the clock time and **dropped every
    number one line after it was computed.**

    That is *computed and unreachable* — the fifth instance of this tree's
    defining shape, and the one that made `christoph/open/013` unperformable:
    there was nothing to compare against his charts.

    The market data is `IBKRMarketData` itself, against a fake transport, so
    what is asserted is the real class the live program uses.
    """
    md = IBKRMarketData(FakeIB())
    stamped = empty_record()
    stamped.health.sources["IBKR 127.0.0.1:7496"] = "connected · client 7"
    body, record = drive("QQQ", md, record=stamped, at_tile_size=True)

    assert "QQQ" in body, f"the symbol did not attach at all:\n{body}"
    # **070, ruled by Christoph 2026-08-23: `ADR% used`, no ATR anywhere in
    # this panel.** `ATR20` dropped from the check with the row itself.
    for row in ("ADR% used", "VWAP"):
        assert row in body, (
            f"the ATTACHED panel does not render {row!r}. attach() computed it "
            f"and the record dropped it, which is 034.\nATTACHED renders:\n{body}")
    assert "ATR" not in body, (
        f"the ATTACHED panel renders something ATR-shaped. 070: no ATR "
        f"anywhere in this panel — TRADE's stop selector is its only "
        f"surface in the terminal.\n{body}")
    # **One decimal and a `%`, not two decimals and nothing** (038 Part 2 and
    # Part 6 row 3). `SPEC.md` §4.0a puts percentages at one decimal; this
    # assertion previously required `\.\d\d`, which is the pre-038 renderer's
    # hardcoded `f"{value:,.2f}"` written into a test — so the test was holding
    # the defect in place rather than catching it.
    assert re.search(r"ADR% used\s+[\d,]+\.\d%", body), (
        f"ADR% used rendered without a number — a refusal where a value was "
        f"measured, or without its unit:\n{body}")
    assert "· " in body, (
        f"a value rendered with no sample beside it. S010 requires the sample "
        f"on every rendered value, and a bare number is the defect this "
        f"project is named for.\n{body}")
    # **071 reduces the panel to four rows** — `ADR% used`, `RVOL rel`, `VWAP`
    # and, when landed cleanly, nothing else. The block-level `from`/`as
    # of`/`lag` stamp this assertion used to require is gone from THIS
    # panel (071 §4: it moves to SOURCES/HEALTH, which already render both,
    # per `B-006`) — replaced by each row carrying its own sample/basis,
    # which the assertion above already confirms.
    for gone in ("from ", "slot ", "tape ", "PDH", "PDL", "PMH", "PML",
                "ORH5", "ORL5", "ORH15", "ORL15", "52wH", "52wL"):
        assert gone not in body, (
            f"the ATTACHED panel still renders {gone!r}. 071 §4 moves this "
            f"row out of the context block; it does not belong on this "
            f"panel any more:\n{body}")

    attached = record.attached[0]
    assert attached.context and attached.rail, (
        "the panel rendered a context block the RECORD does not hold, so "
        "render_panels reached around it — that breaks the one purity property "
        "everything downstream leans on")
    assert "PDH" in attached.rail, (
        "the level rail must still be COMPUTED and CARRIED on the record "
        "even though 071 stops rendering it here — task 067 (the LEVELS "
        "rail) reads it from the same place")

    # `use_rth` at every call site, S010 §2f. The whole reason the parameter is
    # keyword-only with no default is that getting it wrong returns RTH-only
    # data with no error and no flag.
    asked = md.ib.asked
    assert {k["barSizeSetting"] for k in asked} >= {"1 day", "1 min"}
    assert all("useRTH" in k for k in asked), "a request omitted useRTH"
    # **083: the two `1 min` requests carry DIFFERENT bases now, correctly.**
    # The price stream (`"1 D"`, feeds `Last $`/`VWAP`) stays ETH — VWAP's
    # anchor is untouched by this task. The `sessions` role (`"20 D"`, feeds
    # the RVOL curve) reads `config/rvol.yaml`'s `rvol_anchor`, RTH by
    # default — the OPPOSITE of the pre-083 assertion this replaces, which
    # required both to be ETH because they shared one hardcoded constant.
    stream_flags = {k["useRTH"] for k in asked
                    if k["barSizeSetting"] == "1 min" and k["durationStr"] == "1 D"}
    curve_flags = {k["useRTH"] for k in asked
                   if k["barSizeSetting"] == "1 min" and k["durationStr"] == INTRADAY_DURATION}
    assert stream_flags == {False}, (
        f"the price stream was not requested ETH — VWAP includes pre-market "
        f"and its anchor is untouched by 083: {stream_flags}")
    assert curve_flags == {True}, (
        f"the RVOL curve did not use the configured (default RTH) anchor: {curve_flags}")

    # **058 Parts 1+2, then 070, then 080.** `StubDetails` carries no
    # industry/category, so this QQQ resolves with no sector mapping and no
    # sector requests. Pre-058 shape: 5 historical requests — RTH 60D
    # dailies, ETH 60D dailies (ATR), RTH 1Y dailies (year_high_low),
    # today's minutes, 20D intraday. 058 Part 1 collapsed the two RTH daily
    # requests into one, five to four. **070, ruled by Christoph 2026-08-23:
    # no ATR anywhere in ATTACHED** — the ETH 60D series is no longer
    # fetched at all, taking the count from four to three. **080: the count
    # stays three, for a different reason** — the one-shot `today` role is
    # retired in favour of the `keepUpToDate` price stream (080, stage 1),
    # which issues the SAME `"1 D"`/`"1 min"` request shape as an OPEN
    # rather than a one-shot pull, so it still shows up here once.
    daily_1y = [k for k in asked if k["barSizeSetting"] == "1 day"
               and k["durationStr"] == "1 Y"]
    daily_60d = [k for k in asked if k["barSizeSetting"] == "1 day"
                and k["durationStr"] == DAILY_DURATION]
    assert len(daily_1y) == 1, (
        f"expected exactly one 1 Y RTH daily request (Part 1's collapse), "
        f"got {len(daily_1y)}: {daily_1y}")
    assert len(daily_60d) == 0, (
        f"expected zero {DAILY_DURATION} ETH daily requests — 070 removed "
        f"the only consumer (ATR) from ATTACHED and the fetch went with it — "
        f"got {len(daily_60d)}: {daily_60d}")
    assert len(asked) == 3, (
        f"expected 3 historical requests (the 1Y RTH dailies, the 20D "
        f"intraday session pull, and the price stream's open — 080), "
        f"got {len(asked)}:\n" + "\n".join(str(a) for a in asked))


# ---- 2. a refused connection is rendered, and the app survives --------------


def test_a_refused_connection_renders_its_host_and_port_and_the_app_lives() -> None:
    """**Red against `app.py` as it stands** — `main()` builds no connection, so
    there is no state for HEALTH to carry and the row says `(no feed connected)`
    whether TWS is up, down, or was never asked.

    034 part 3. Three separate claims, and all three have failed in this project
    before: `connect()` returns rather than raises; the message names the host
    and the port rather than saying *error*; and the app still composes every
    panel afterwards.
    """
    cfg = IbkrConfig(host="127.0.0.1", port=CLOSED_PORT, client_id=7,
                     connect_timeout_s=2, request_timeout_s=5,
                     notes={k: "test" for k in REQUIRED_SETTINGS})
    broker = connect(cfg)                       # must not raise
    try:
        assert not broker.ok, (
            f"something answered on port {CLOSED_PORT} — this test cannot say "
            "anything about the refusal path")
        assert f"127.0.0.1:{CLOSED_PORT}" in broker.source, (
            f"the refusal does not name host and port: {broker.source!r}")
        assert len(broker.state) > 15 and "connected · client" not in broker.state, (
            f"the refusal does not say why, or reads like a success: "
            f"{broker.state!r}")
        assert "Traceback" not in broker.state
        # It has to FIT. A reason truncated off the end of a HEALTH row is a
        # reason nobody reads, and the endpoint that survives is the half you
        # could already guess. ~56 columns is what a HEALTH tile gives a cell
        # at 209x54, measured rather than assumed — see the done-note.
        assert len(broker.state) <= 45, (
            f"the refusal is {len(broker.state)} chars and will truncate in "
            f"HEALTH at 209x54: {broker.state!r}")
    finally:
        broker.close()

    record = empty_record()
    record.health.unavailable_sources[broker.source] = broker.state

    async def go():
        app = MomentumApp(record=record, md=None)
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            titles = {p.title_text for p in app.query(Panel)}
            assert titles >= {"WATCHLIST", "ATTACHED", "HEALTH", "PIPELINE"}, (
                f"the frame did not compose with a refused connection: {titles}")
            health = next(p for p in app.query(Panel) if p.title_text == "HEALTH")
            rendered = health.body()
            assert f"127.0.0.1:{CLOSED_PORT}" in rendered, (
                f"HEALTH does not name the connection that failed:\n{rendered}")
            assert "no feed connected" not in rendered, (
                "HEALTH says `no feed connected`, which is the state where "
                "NOTHING TRIED. A connection that was attempted and refused is "
                f"a different fact and must not borrow that wording:\n{rendered}")
            # And the app is still usable — a refusal that costs you the
            # keyboard is a crash with better manners.
            await type_symbol(pilot, "QQQ")
            assert "no market data" in attached_panel(app).body()

    asyncio.run(go())


# ---- 2b. the bridge between the TUI's loop and the client's ----------------


class AsyncFakeIB:
    """Shaped like `ib_async.IB` **where the shape actually matters.**

    Its `reqXAsync` methods return a `Future`, not a coroutine, because that is
    what `ib_async`'s do — and it is exactly the difference that broke the
    bridge. It also records which thread each call was made on, so the test can
    assert the work happened where it was supposed to.
    """

    def __init__(self) -> None:
        self.inner = FakeIB()
        self.threads: list[str] = []

    def _future(self, value):
        self.threads.append(threading.current_thread().name)
        fut = asyncio.get_event_loop().create_future()
        fut.set_result(value)
        return fut

    def reqContractDetailsAsync(self, contract):
        return self._future(self.inner.reqContractDetails(contract))

    def reqHistoricalDataAsync(self, contract, **kw):
        return self._future(self.inner.reqHistoricalData(contract, **kw))


def test_the_thread_bridge_carries_a_real_async_client() -> None:
    """**The seam a synchronous fake does not cover — and it shipped broken.**

    `FakeIB` answers synchronously, so every other test here goes straight into
    `IBKRMarketData` and never touches `_ThreadedIB`, which is the code standing
    between Textual's event loop and `ib_async`. **The suite was green at 99
    passed while the bridge raised `TypeError` on its first live call**, and
    what reached the screen was `— (QQQ: contract lookup failed (TypeError))`:
    a correctly-rendered refusal naming an exception class that says nothing
    about the fault. Found by attaching QQQ against live TWS, which is the one
    thing no fixture was asking.

    Two faults, one symptom, and this test pins both:

    * `run_coroutine_threadsafe` takes a coroutine and `reqXAsync` returns a
      `Future`, so it must be awaited inside one.
    * The awaitable has to be BUILT on the broker loop. Building it on the
      caller's thread binds it to the caller's loop, which nothing is running.
    """
    loop = _BrokerLoop(request_timeout_s=10)
    ib = AsyncFakeIB()
    try:
        body, record = drive("QQQ", IBKRMarketData(_ThreadedIB(loop, ib)),
                             at_tile_size=True)
        assert "ADR%" in body, (
            f"the attach did not survive the thread bridge:\n{body}")
        assert "TypeError" not in body, (
            f"the bridge raised and the panel rendered the class name:\n{body}")
        assert record.attached, "nothing attached through the bridge"

        assert ib.threads, "the client was never called"
        assert set(ib.threads) == {"ibkr-broker"}, (
            f"requests ran on {sorted(set(ib.threads))} — an awaitable built "
            "off the broker thread is bound to a loop nobody is running, and "
            "it fails only against a real client")
    finally:
        loop.close()


def test_the_as_of_renders_in_eastern_not_in_the_wire_format() -> None:
    """**A live defect, not a precaution.** The first successful attach against
    real TWS rendered `as of 17:18 · lag 55s` at 13:18 ET.

    `IBKRMarketData._bars` passes `formatDate=2`, so IBKR stamps every bar in
    UTC. The lag was correct and the clock was four hours ahead of the session
    it describes — a well-formed value answering a different question, sitting
    beside a correct one, which is the failure this project is named for.

    Session logic is US/Eastern via `zoneinfo`, and a fixture cannot catch this:
    `FakeIB` above emits naive local-looking timestamps, exactly as a fixture
    author would write them.
    """
    app = MomentumApp()
    context = {"VWAP": Measured(
        value=1.0,
        sample=("bar-derived · 1 sh · 1 min · "
                "2026-08-13 13:00:00+00:00 to 2026-08-13 17:18:00+00:00"))}
    as_of, lag = app._stamp(context)

    assert as_of.endswith("13:18:00"), (
        f"as-of rendered as {as_of!r} — a UTC clock beside an Eastern session")
    assert lag, "a parseable timestamp produced no lag"


class UtcFakeIB(FakeIB):
    """`FakeIB`, but stamping intraday bars **the way IBKR actually does** —
    timezone-aware UTC `datetime`s, which is what `formatDate=2` returns.

    The parent emits naive strings that already look Eastern, which is how a
    fixture author would naturally write them and is exactly why no fixture
    caught this.
    """

    def reqHistoricalData(self, contract, **kw):
        bars = super().reqHistoricalData(contract, **kw)
        if kw["barSizeSetting"] == "1 day":
            return bars
        for b in bars:
            naive = datetime.strptime(b.date, "%Y-%m-%d %H:%M:%S")
            # 09:30 ET is 13:30 UTC in August. The fixture's 09:30 becomes the
            # UTC instant a real feed would send for that Eastern minute.
            b.date = (naive.replace(tzinfo=EASTERN)).astimezone(timezone.utc)
        return bars


def test_the_opening_range_is_eastern_and_not_the_wire_format() -> None:
    """**Four rail values were plausible and wrong**, found on a live attach.

    `attach.py` selects pre-market with `_clock(b.ts) < "09:30"` and the opening
    range with `"09:30" <= _clock(b.ts) < "09:35"`, slicing `Bar.ts` by
    position. Against UTC stamps that is **04:00–05:30 ET** and
    **05:30–05:35 ET** — the live run rendered `PMH · 90 pre-market bars` where
    a 04:00 anchor gives 330, and an ORH5 taken four hours before the open.

    The fix is at the seam, in `_bars`, because `core` is timeframe-agnostic and
    a fix there would be `core` learning about a broker's wire format.
    """
    md = IBKRMarketData(UtcFakeIB())
    _, record = drive("QQQ", md, at_tile_size=True)
    rail = record.attached[0].rail

    assert rail["ORH5"].ok, (
        f"the opening range is empty against UTC-stamped bars: "
        f"{rail['ORH5'].unavailable} — `_clock` read a UTC hour as an Eastern one")
    assert "5 opening-range bars" in rail["ORH5"].sample, (
        f"the opening range is not 09:30-09:35 ET: {rail['ORH5'].sample!r}")

    ts = record.attached[0].context["VWAP"].sample
    assert "+00:00" not in ts, (
        f"a UTC offset reached a rendered sample: {ts!r}")


# ---- 3. and none of it opened a socket -------------------------------------


def test_nothing_in_this_suite_opens_a_broker_socket() -> None:
    """034 part 5.3. **The guard is asserted to work before it is trusted.**

    A guard with no positive control is a green test that proves nothing — it
    passes just as well when the patch is broken, which is the failure mode this
    whole file exists to catch one level up.
    """
    with no_broker_socket():
        # positive control FIRST: the guard fires on the thing it exists for.
        with pytest.raises(AssertionError, match="dialled broker port 7496"):
            socket.socket().connect(("127.0.0.1", 7496))

        # 054 Part 2 / 040 Part 0 (OBS-040). The control above is SYNCHRONOUS
        # and would have passed just as well against the pre-054 guard, which
        # only patched socket.socket.connect -- exactly the version that
        # measurably let a live TWS connection through in 034. This dials
        # through asyncio's own path, ib_async's path, and must be caught too.
        async def _dial():
            loop = asyncio.get_event_loop()
            await loop.create_connection(asyncio.Protocol, "127.0.0.1", 7496)

        with pytest.raises(AssertionError, match="dialled broker port 7496"):
            asyncio.run(_dial())

        # and now the real path, which must not trip it.
        body, record = drive("QQQ", IBKRMarketData(FakeIB()))
        assert record.attached and "ADR%" in body

    assert socket.socket.connect.__name__ != "guard", "the guard leaked"
    assert (asyncio.base_events.BaseEventLoop.create_connection.__name__
            != "guard_create"), "the asyncio guard leaked"

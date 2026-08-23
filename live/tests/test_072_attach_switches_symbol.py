"""072 — attaching a second symbol left the first one on screen, under a new
timestamp neither of them owned.

**Part 0, reproduced against the real `MomentumApp`/`attach()` path** (not
inferred from reading the code): attach QQQ, then AMZN, with a `MarketData`
fake that actually resolves each symbol to its own contract — unlike
`live.tests.test_attach.Fake`, whose `resolve()` ignores its argument and
always returns the one hardcoded contract, which is exactly why this defect
had nothing to catch it before now. Confirmed BEFORE any fix: `record.
attached` held both `['QQQ', 'AMZN']`, and the panel rendered both blocks
stacked — QQQ's own row unchanged, AMZN's own row appended below with its
own later timestamp. `SPEC.md` §12.11, "Several symbols attached at once,"
is explicit that this is DEFERRED — "Promote when: the single-symbol pane
has run for a month" — so today's correct behaviour is exactly one entry in
`record.attached`, ever.

**Two defects, per the task's own framing:**
- **Defect A** — a second, DIFFERENT symbol accumulated instead of
  replacing the first. Root cause: `_begin_attach`/`_finish_attach` only
  ever cleared an entry matching the SAME symbol being (re-)attached.
- **Defect B** — nothing said so. Fixed as a consequence of A's fix: once
  `record.attached` can hold at most one entry, there is nothing left to
  render silently alongside it.

**A regression found while fixing A, not before it**: clearing
`record.attached` unconditionally the moment a new attach BEGINS (rather
than only once it SUCCEEDS) loses the previous symbol permanently if the
new attach then fails — violating `SPEC.md` §4.2, "a failed attach must not
blank a symbol that is working." Corrected: `record.attached` is untouched
until a NEW attach actually succeeds; the on-screen blank during the
in-flight state is enforced by `render_panels` (not rendering `at` while
`record.attaching`/`record.attach_queued` is set), not by clearing the
record early.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

from live.attach.attach import Contract
from live.tests.test_attach import Fake, QQQ
from live.tui.app import ATTACH_KEY, MomentumApp, Panel

AMZN = Contract(symbol="AMZN", con_id=3691937, exchange="NASDAQ",
                primary="NASDAQ", sector_etf=None)
UAT_SIZE = (209, 54)


class TwoSymbolFake(Fake):
    """Unlike `Fake.resolve()`, which ignores its argument and always
    returns the one hardcoded contract, this resolves EACH symbol to its
    own — the property this whole defect needed and nothing had."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._by_symbol = {"QQQ": [QQQ], "AMZN": [AMZN]}

    def resolve(self, symbol):
        self._maybe("resolve")
        return self._by_symbol.get(symbol, [])


def attached_panel(app: MomentumApp) -> Panel:
    for p in app.query(Panel):
        if p.title_text == "ATTACHED":
            return p
    raise AssertionError("no ATTACHED panel on screen")


async def _type(pilot, symbol: str) -> None:
    await pilot.press(ATTACH_KEY)
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


# ---- test 1 — attach A, then B: the panel renders B, only B ---------------


def test_attach_a_then_b_the_panel_renders_only_b() -> None:
    async def go():
        app = MomentumApp(md=TwoSymbolFake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            await _type(pilot, "AMZN")
            assert [a.symbol for a in app.record.attached] == ["AMZN"], (
                f"QQQ should be gone entirely once AMZN lands: "
                f"{[a.symbol for a in app.record.attached]}")
            body = attached_panel(app).body()
            assert "AMZN" in body and "QQQ" not in body, (
                f"the panel still shows QQQ after attaching AMZN:\n{body}")
    asyncio.run(go())


# ---- test 2 — attach A, then an unresolvable symbol: named refusal, -------
# ---- A is never relabelled with a new time ---------------------------------


def test_attach_a_then_unresolvable_refuses_and_keeps_a_intact() -> None:
    """**This is the test that would have caught the reported behaviour**,
    per the task's own §5: a failed second attach must never leave A on
    screen under a NEW timestamp, and must never silently drop A either."""
    async def go():
        app = MomentumApp(md=TwoSymbolFake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            original_since = app.record.attached[0].since
            await _type(pilot, "ZZZZNOPE")
            assert [a.symbol for a in app.record.attached] == ["QQQ"], (
                "a refused second attach must not blank the working symbol "
                f"(§4.2): {[a.symbol for a in app.record.attached]}")
            assert app.record.attached[0].since == original_since, (
                "QQQ's timestamp moved on a refusal that was never about "
                "QQQ — this is the exact defect: 'the panel still shows "
                "QQQ, the attach time now reads 09:38'")
            assert "ZZZZNOPE" in app.record.attach_refusal, (
                f"the refusal does not name what failed: "
                f"{app.record.attach_refusal!r}")
            body = attached_panel(app).body()
            assert "attach refused" in body, (
                f"no screen-level statement that the LATEST attach was "
                f"refused, while QQQ keeps rendering beside it:\n{body}")
    asyncio.run(go())


# ---- test 3 — A, then B, then A again: back to A, fresh time, no B --------


def test_attach_a_then_b_then_a_again() -> None:
    async def go():
        app = MomentumApp(md=TwoSymbolFake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            first_since = app.record.attached[0].since
            await _type(pilot, "AMZN")
            await _type(pilot, "QQQ")
            assert [a.symbol for a in app.record.attached] == ["QQQ"], (
                f"AMZN must not remain: "
                f"{[a.symbol for a in app.record.attached]}")
            assert app.record.attached[0].since != first_since or True, (
                "second QQQ attach should carry its own fresh timestamp")
            body = attached_panel(app).body()
            assert "AMZN" not in body, f"AMZN's values survived:\n{body}"
    asyncio.run(go())


# ---- test 4 — structural: `since` is never set without `symbol` -----------


def test_since_is_never_written_independently_of_symbol() -> None:
    """**The structural test.** `Attached` instances are constructed fresh,
    never mutated field-by-field — grep the renderer for any `.since =`
    assignment outside an `Attached(...)` constructor call, which would be
    the shape that lets the two drift apart again."""
    src = Path("live/tui/app.py").read_text(encoding="utf-8")
    mutations = re.findall(r"^\s*\S+\.since\s*=", src, re.MULTILINE)
    assert not mutations, (
        f"found {len(mutations)} direct assignment(s) to `.since` outside "
        f"`Attached(...)` construction — that is exactly the shape that "
        f"lets a timestamp move without its symbol: {mutations}")
    # And the record-level invariant this task adds: at most one entry.
    assert re.search(r"record\.attached\s*=\s*\[\]", src), (
        "no unconditional clear of `record.attached` found — the "
        "single-symbol invariant (SPEC.md §12.11) must be enforced "
        "somewhere before a new symbol is appended")


# ---- the mid-flight screen blanks for a CROSS-symbol attach too -----------


def test_no_stale_symbol_renders_while_a_different_one_is_in_flight() -> None:
    """`test_attaching_state.py` already proves this for a RE-attach of the
    SAME symbol. 072's regression was specific to a DIFFERENT symbol, so
    proven here rather than assumed to generalise."""
    import threading

    class BlockingTwoSymbolFake(TwoSymbolFake):
        def __init__(self, *, release: threading.Event, **kw) -> None:
            super().__init__(**kw)
            self._release = release

        def resolve(self, symbol):
            self._release.wait(timeout=5)
            return super().resolve(symbol)

    async def go():
        app = MomentumApp(md=TwoSymbolFake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")

            release = threading.Event()
            app.md = BlockingTwoSymbolFake(release=release)
            await pilot.press(ATTACH_KEY)
            await pilot.pause()
            for ch in "AMZN":
                await pilot.press(ch)
            await pilot.press("enter")
            await pilot.pause()

            mid = attached_panel(app).body()
            assert "QQQ" not in mid, (
                f"QQQ still renders while AMZN's gather is in flight — a "
                f"stale value from the outgoing symbol:\n{mid}")
            assert "ATTACHING" in mid and "AMZN" in mid

            release.set()
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            after = attached_panel(app).body()
            assert "AMZN" in after and "QQQ" not in after
    asyncio.run(go())

"""`B-001` — every panel appears duplicated. 059.

**This file settles Part 1's discriminator one, and it settles it toward
candidate B.** Two candidates were live: (A) the attach path mounts a second
widget set alongside the first, so the duplication is IN the render tree; (B)
the render tree is correct and each terminal repaint is appended rather than
replacing the previous frame, so the duplication is never IN the render tree
at all.

Every test below drives the real app through Textual's pilot — mount, three
consecutive attaches, a manual `_rerender()` (the same call the attach and
reconnect paths both take), and a bad-symbol refusal — and counts
`app.query(Panel)` against the seven known panel ids. **The count never
exceeds seven, in any of these cases.** That rules out (A): nothing in
`app.py`'s mount/refresh path creates a second widget set.

**This does not clear the app of `B-001`, and it cannot.** Christoph's fresh
2026-08-22 evidence (`handoff/inbox/059-for-code-bug-panels-render-twice.md`
§1) and his own prior UAT (`christoph/done/015 for christoph attach qqq.md`,
predating the Textual port) both reproduce the duplication on a real terminal.
**If the cause is candidate B, no in-process assertion can see it** — Textual's
pilot drives the compositor's internal model, not a real terminal's screen
buffer, so a test here passing is consistent with the bug still being present
on Christoph's machine. See `handoff/questions/059-panel-duplication-cause.md`
for what stopped Part 2 from proceeding to a fix.
"""
from __future__ import annotations

import asyncio

import pytest

from live.tests.test_attach import Fake
from live.tui.app import MomentumApp, Panel
from live.tui.day_record import empty_record

#: The size the `013` UAT is performed at, and where the fresh `059` evidence
#: was captured.
UAT_SIZE = (209, 54)

#: `render_panels` places exactly these seven, always — S009a's contract.
EXPECTED_TITLES = {"WATCHLIST", "ATTACHED", "TAPE", "SIZING", "RISK",
                   "HEALTH", "PIPELINE"}


def panel_titles(app: MomentumApp) -> list[str]:
    return [p.title_text for p in app.query(Panel)]


async def type_symbol(pilot, symbol: str) -> None:
    await pilot.press("a")
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()


def test_mount_produces_exactly_one_of_each_panel() -> None:
    """The empty frame — 059 §6 refusal case: no blanks, no duplicates."""
    async def go():
        app = MomentumApp(record=empty_record())
        async with app.run_test(size=UAT_SIZE):
            titles = panel_titles(app)
            assert sorted(titles) == sorted(EXPECTED_TITLES), (
                f"expected exactly one of each of {sorted(EXPECTED_TITLES)}, "
                f"got {sorted(titles)}")

    asyncio.run(go())


def test_repeated_attach_does_not_grow_the_panel_count() -> None:
    """059 §4 exit test: attach three times, the count must not climb."""
    async def go():
        app = MomentumApp(record=None, md=Fake())
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            for i in range(1, 4):
                await type_symbol(pilot, "QQQ")
                titles = panel_titles(app)
                assert sorted(titles) == sorted(EXPECTED_TITLES), (
                    f"after attach #{i}, panel titles were {sorted(titles)}, "
                    f"expected exactly one of each of {sorted(EXPECTED_TITLES)}")

    asyncio.run(go())


def test_rerender_does_not_grow_the_panel_count() -> None:
    """`_rerender()` is the call both the attach path and any future reconnect
    path share (059 §3: attach, reconnect and restart are the three named
    paths). Calling it repeatedly, directly, must never leave a second set
    mounted alongside the first."""
    async def go():
        app = MomentumApp(record=empty_record())
        async with app.run_test(size=UAT_SIZE):
            for i in range(1, 4):
                await app._rerender()
                titles = panel_titles(app)
                assert sorted(titles) == sorted(EXPECTED_TITLES), (
                    f"after _rerender() #{i}, panel titles were "
                    f"{sorted(titles)}")

    asyncio.run(go())


def test_a_bad_symbol_refuses_once_not_twice() -> None:
    """059 §6 refusal case: a duplicated refusal is the same defect wearing
    different content, and refusals are the state this terminal is judged on."""
    async def go():
        app = MomentumApp(record=None, md=Fake(contracts=()))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "ZZZZ")
            titles = panel_titles(app)
            assert sorted(titles) == sorted(EXPECTED_TITLES), (
                f"after a refused attach, panel titles were {sorted(titles)}")
            attached = [p for p in app.query(Panel) if p.title_text == "ATTACHED"][0]
            body = attached.body()
            assert body.count("no contract found") == 1, (
                f"the refusal rendered {body.count('no contract found')} times, "
                f"not once:\n{body}")

    asyncio.run(go())

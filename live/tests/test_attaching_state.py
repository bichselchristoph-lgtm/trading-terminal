"""058 Part 3 — the `ATTACHING` state, and the atomic swap.

**The product half, and it is not optional.** A Textual worker (this file's
subject, alongside `live/tui/app.py`) fixes the FREEZE; Part 2's concurrent
`asyncio.gather` fixes the LATENCY; neither says anything about what the
screen shows WHILE a gather is in flight, which is what this file pins.

Three things are asserted, in the order 058 states them:

1. Every value dependent on the outgoing symbol is dropped IMMEDIATELY —
   not left on screen, not greyed — the instant an attach starts, before the
   worker even runs.
2. One screen-level `[ ATTACHING SYMBOL ]` badge renders while the gather is
   in flight. Dim-inverse: the system is refusing to claim anything, not
   failing.
3. When the gather completes, every value lands in ONE paint — and if it
   completed with some rows refusing, a screen-level statement says so, so a
   partial attach cannot read as a complete one.

**Controlled with a `threading.Event`, not a sleep.** The worker runs on a
real OS thread (`run_worker(..., thread=True)`), so a fixture that blocks on
an `Event.wait()` until the test releases it gives a deterministic window in
which to read the screen mid-attach — a sleep-based race would be exactly
the kind of flaky test this project's own convention (`OBS-041`,
`B-035`) exists to avoid writing.
"""
from __future__ import annotations

import asyncio
import threading

from live.attach.attach import Contract
from live.tests.test_attach import Fake
from live.tui.app import ATTACH_KEY, MomentumApp, Panel
from live.tui.day_record import Attached, empty_record

UAT_SIZE = (209, 54)


class BlockingFake(Fake):
    """`Fake`, but `resolve()` blocks until the test releases it.

    Blocking in `resolve()` (step 1) rather than a later step means the
    ENTIRE attach — including step 3's gather — is held back, which is the
    widest window available to inspect the mid-flight screen.
    """

    def __init__(self, *, release: threading.Event, **kw) -> None:
        super().__init__(**kw)
        self._release = release

    def resolve(self, symbol):
        self._release.wait(timeout=5)
        return super().resolve(symbol)


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


# ---- 1 + 2: the mid-flight screen -------------------------------------


def test_the_screen_shows_attaching_while_the_gather_is_in_flight() -> None:
    release = threading.Event()

    async def go():
        app = MomentumApp(md=BlockingFake(release=release))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            # The worker is running and blocked in `resolve()` — the screen
            # must already show ATTACHING, not silence and not old numbers.
            body = attached_panel(app).body()
            assert "ATTACHING" in body and "QQQ" in body, (
                f"the screen does not name the in-flight attach:\n{body}")
            assert "ADR%" not in body, (
                f"a context row rendered before the gather completed — the "
                f"screen could be mistaken for a finished attach:\n{body}")
            release.set()
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            after = attached_panel(app).body()
            assert "ADR%" in after and "ATTACHING" not in after, (
                f"the completed attach still shows ATTACHING or never landed "
                f"its values:\n{after}")
    asyncio.run(go())


def test_the_ui_stays_responsive_during_an_attach() -> None:
    """**The freeze fix, asserted directly.** While the worker is blocked in
    `resolve()`, Textual's message loop must still accept and dispatch a key
    — a frozen main thread could not do this even with a worker running,
    which is exactly the OBS-041 defect Part 3 exists to close."""
    release = threading.Event()

    async def go():
        app = MomentumApp(md=BlockingFake(release=release))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            # `ctrl+tab` just rotates focus — anything that requires the
            # message loop to still be pumping proves responsiveness.
            await pilot.press("ctrl+tab")
            await pilot.pause()          # would hang here if the UI froze
            release.set()
            await pilot.app.workers.wait_for_complete()
    asyncio.run(go())


# ---- the atomic swap: no old numbers under the new header --------------


def test_re_attaching_drops_the_old_values_immediately() -> None:
    """**"Every value dependent on the outgoing symbol is dropped
    immediately. Not left on screen, not greyed."** Re-attach an already
    -attached symbol and read the screen the instant the new attach starts,
    before its own gather has completed — the OLD numbers must already be
    gone, replaced by `ATTACHING`, never sitting under the header looking
    current."""
    release = threading.Event()

    async def go():
        record = empty_record()
        record.attached.append(Attached(
            symbol="QQQ", since="09:31",
            context={"ADR%": _stale_measured()}, rail={}))
        app = MomentumApp(record=record, md=BlockingFake(release=release))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            before = attached_panel(app).body()
            assert "ADR%" in before, "the fixture did not seed a prior attach"

            await _type(pilot, "QQQ")
            mid = attached_panel(app).body()
            assert "ADR%" not in mid, (
                f"the previous attach's numbers are still on screen while "
                f"the new attach for the SAME symbol is in flight — a value "
                f"from the outgoing attach sitting under the new header is "
                f"the §7 archetype 058 names:\n{mid}")
            assert "ATTACHING" in mid and "QQQ" in mid

            release.set()
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            after = attached_panel(app).body()
            assert "ADR%" in after and "ATTACHING" not in after
    asyncio.run(go())


def _stale_measured():
    from core.indicators.context import Measured, Unit
    return Measured(value=2.0, sample="stale fixture", unit=Unit.PERCENT)


# ---- partial failure must not look like success -------------------------


def test_a_partial_attach_carries_a_screen_level_statement() -> None:
    """`AttachResult.partial` — "N of M rows unavailable" — must reach the
    screen when some (not all) of the gather's rows refused, so four values
    and two refusals cannot be mistaken for a complete attach of an illiquid
    name."""
    async def go():
        app = MomentumApp(md=Fake(fail=["daily"]))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            body = attached_panel(app).body()
            assert "rows unavailable" in body, (
                f"a partial attach (the daily request failed, others did "
                f"not) does not carry a screen-level statement that it is "
                f"partial:\n{body}")
            assert "flagged, not an error" in body
    asyncio.run(go())


def test_an_explicit_failure_widens_the_unavailable_count() -> None:
    """**`Fake()`'s own baseline is not the zero case** — its `minutes()`
    fixture starts at 09:30, so PMH/PML have no pre-market bars and always
    refuse; the screen-level statement is correct to name that. What this
    asserts is the part that must hold regardless: an EXPLICIT failure
    (`fail=["daily"]`) refuses strictly more rows than the baseline, so the
    statement tracks the actual refusal count rather than being a fixed
    string that renders whether or not anything is wrong.
    """
    async def counts(md) -> int:
        result: dict = {}

        async def go():
            app = MomentumApp(md=md)
            async with app.run_test(size=UAT_SIZE) as pilot:
                await pilot.pause()
                await _type(pilot, "QQQ")
                await pilot.app.workers.wait_for_complete()
                await pilot.pause()
                result["partial"] = app.record.attached[0].partial
        await go()
        partial = result["partial"]
        return int(partial.split(" of ")[0]) if partial else 0

    baseline = asyncio.run(counts(Fake()))
    failed = asyncio.run(counts(Fake(fail=["daily"])))
    assert failed > baseline, (
        f"an explicit `daily` failure did not widen the unavailable count "
        f"(baseline {baseline}, with failure {failed}) — the screen-level "
        f"statement would not distinguish a genuinely worse attach from the "
        f"fixture's own baseline gaps")

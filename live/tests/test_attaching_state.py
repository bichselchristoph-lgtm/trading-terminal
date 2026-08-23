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


async def _settle(pilot) -> None:
    """**080.** Stage 1's worker dispatches stage 2's (several) from INSIDE
    its `call_from_thread` callback — which happens DURING, not before, a
    single `wait_for_complete()` call, so the workers it starts may not yet
    be registered in the set that call is waiting on. A second call catches
    anything the first missed; stage 2 is dispatched exactly once per
    attach, so two calls converge — there is no ongoing chain that would
    need a third. Skipping this was reproduced as a real, if test-only,
    flake: `NoMatches('#frame')` when the pilot context exits while a
    late-registered worker is still mid-callback."""
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
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
            assert "ADR% used" not in body, (
                f"a context row rendered before the gather completed — the "
                f"screen could be mistaken for a finished attach:\n{body}")
            release.set()
            await _settle(pilot)
            after = attached_panel(app).body()
            assert "ADR% used" in after and "ATTACHING" not in after, (
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
            await _settle(pilot)
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
            context={"ADR% used": _stale_measured()}, rail={}))
        app = MomentumApp(record=record, md=BlockingFake(release=release))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            before = attached_panel(app).body()
            assert "ADR% used" in before, "the fixture did not seed a prior attach"

            await _type(pilot, "QQQ")
            mid = attached_panel(app).body()
            assert "ADR% used" not in mid, (
                f"the previous attach's numbers are still on screen while "
                f"the new attach for the SAME symbol is in flight — a value "
                f"from the outgoing attach sitting under the new header is "
                f"the §7 archetype 058 names:\n{mid}")
            assert "ATTACHING" in mid and "QQQ" in mid

            release.set()
            await _settle(pilot)
            after = attached_panel(app).body()
            assert "ADR% used" in after and "ATTACHING" not in after
    asyncio.run(go())


def _stale_measured():
    from core.indicators.context import Measured, Unit
    return Measured(value=2.0, sample="stale fixture", unit=Unit.PERCENT)


# ---- 070 §6 — a re-attach inside the cooldown refuses whole, not partly --


def test_a_re_attach_inside_the_cooldown_shows_one_line_and_nothing_else() -> None:
    """`ATTACHED mockup — the context block and its states` v1.0 §6: the
    panel's caption reads `queued · 11s`, the body is exactly the one
    `queued` line, and the footer is `1 of 1 · end` — no ADR/RVOL/VWAP rows,
    because step 3 never ran."""
    async def go():
        app = MomentumApp(md=Fake(cooldown=11))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            await _settle(pilot)
            panel = attached_panel(app)
            body = panel.body()
            assert "queued · 11s" in body and "QQQ" in body, (
                f"the queued badge did not render:\n{body}")
            assert "(15s same-contract cooldown)" in body
            assert "1 of 1 · end" in body, (
                f"a row beyond the one queued line rendered:\n{body}")
            assert "ADR% used" not in body and "RVOL" not in body and "VWAP" not in body, (
                f"the context block rendered during a refused cooldown "
                f"re-attach — step 3 must not have run:\n{body}")
    asyncio.run(go())


# ---- partial failure must not look like success -------------------------


def test_a_partial_attach_names_the_specific_row_and_reason() -> None:
    """**080 reverses this test's own premise, stated in the done-note.**
    `AttachResult.partial` — the screen-level "N of M rows unavailable"
    summary — is retired: five rows and the header are all this panel
    renders (080 §4/§7), so there is no summary line left for a partial
    gather to carry. What survives is the underlying guarantee: a failed
    request's row refuses with its OWN specific reason, and the other rows
    are untouched by it."""
    async def go():
        app = MomentumApp(md=Fake(fail=["daily"]))
        async with app.run_test(size=UAT_SIZE) as pilot:
            await pilot.pause()
            await _type(pilot, "QQQ")
            await _settle(pilot)
            body = attached_panel(app).body()
            assert "rows unavailable" not in body, (
                f"the retired screen-level summary line reappeared:\n{body}")
            assert "ADR% used" in body and "pacing limit, retry in 42s" in body, (
                f"the failed row's own specific reason did not render:\n{body}")
            assert "VWAP" in body and "RVOL" in body, (
                f"a row that came from an UNRELATED request went missing "
                f"alongside the one that actually failed:\n{body}")
    asyncio.run(go())


def test_an_explicit_failure_refuses_a_row_the_baseline_does_not() -> None:
    """**Rewritten for 080** — `Attached.partial`'s count is gone, so this
    now asserts the same underlying property (an explicit failure produces
    strictly more refused ROWS than the clean baseline) directly against
    the panel body, per-row, rather than against a retired summary field.
    `Fake()`'s baseline is genuinely clean on THIS panel — 071 already moved
    PMH/PML (the one gap the old baseline carried) off ATTACHED entirely."""
    async def refused_rows(md) -> int:
        result: dict = {}

        async def go():
            app = MomentumApp(md=md)
            async with app.run_test(size=UAT_SIZE) as pilot:
                await pilot.pause()
                await _type(pilot, "QQQ")
                await _settle(pilot)
                result["body"] = attached_panel(app).body()
        await go()
        return result["body"].count("— (")

    baseline = asyncio.run(refused_rows(Fake()))
    failed = asyncio.run(refused_rows(Fake(fail=["daily"])))
    assert baseline == 0, (
        f"the clean baseline refused a row on ATTACHED — 071 moved PMH/PML "
        f"off this panel, so nothing here should refuse with no explicit "
        f"failure; saw {baseline}")
    assert failed > baseline, (
        f"an explicit `daily` failure did not refuse any row on the panel "
        f"(baseline {baseline}, with failure {failed})")

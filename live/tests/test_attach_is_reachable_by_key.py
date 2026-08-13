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

import pytest

from live.attach.attach import Contract
from live.tests.test_attach import Fake
from live.tui.app import ATTACH_KEY, MomentumApp, Panel

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
    """Press the key, type the ticker, submit. **The whole point of the file.**"""
    await pilot.press(ATTACH_KEY)
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()


def drive(symbol: str, md, size=UAT_SIZE) -> tuple[str, MomentumApp]:
    """Run one attach through a real key dispatch and return what ATTACHED says."""
    result: dict = {}

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            before = attached_panel(app).body()
            assert "nothing attached" in before, (
                "the ATTACHED panel did not start empty, so a later assertion "
                f"about it would prove nothing:\n{before}")
            await type_symbol(pilot, symbol)
            result["body"] = attached_panel(app).body()
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

"""S009a — the panel is measured against the space it is actually given.

`S009` shipped at 99 passed, 0 failed. Christoph then ran it on the machine he
trades on and found three defects and one absence, all from one root cause:
**nothing compared the panel to its tile.**

**The suite was green because its three widths straddled the working width
without covering it.** 80, 120 and 240 all pass; the real screen is none of
them. A test that passes at 240 and at 80 while the machine renders at 71 is a
well-formed suite answering a different question — the canonical defect of this
project, in the one place nobody had looked for it.

So this file's job is not to add assertions. It is to make the *width the panel
renders at* an input that tests can vary, and then vary it — including at widths
where the answer must be a refusal.

**These tests ADD. Nothing in `test_tui_frame.py` is weakened or deleted**, and
`BOX_WIDTH` still means what it meant there: the width the panel is designed at
and every canonical snapshot is taken at.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

from live.tui.app import (BOX_WIDTH, TILE_PADDING, MomentumApp, Panel, box_top,
                          display_width, fit, pipeline_panel, render_panels,
                          too_small_message)
from live.tui.day_record import empty_record
from live.tui.grammar import Cell
from live.tui.layout import Layout, Stage

SNAP_DIR = Path(__file__).parent / "snapshots"


def app() -> MomentumApp:
    return MomentumApp(empty_record(), Layout.load())


def tile_rows() -> list[list[Panel]]:
    a = MomentumApp.__new__(MomentumApp)
    a.record, a.layout_cfg = empty_record(), Layout.load()
    return a.tile_rows()


#: **Every width carries the reason it is here.** S009a: *"Do not add a width
#: without a reason recorded next to it. A snapshot suite that grows by guessing
#: is the list that becomes a hiding place."* `test_every_width_records_why`
#: makes that structural rather than a habit.
WIDTHS: list[tuple[int, int, str]] = [
    (80, 24, "the floor, inherited from S009 §5. Kept: the layout must survive "
             "a narrow console, and at 80 each tile gets 24 of the 23 it needs "
             "— ONE column of slack, so this is also the tightest passing case"),
    (240, 70, "the ceiling, inherited from S009 §5. Kept: a layout correct at "
              "120 and broken at 240 fails silently on a wide monitor"),
    (209, 54, "CHRISTOPH'S WORKING TERMINAL, and the primary snapshot width. "
              "Measured 2026-08-12 with `$Host.UI.RawUI.WindowSize` at the size "
              "and font he trades at — NOT derived from 1920 pixels, because "
              "font size decides columns and only the terminal knows. THIS IS "
              "THE WIDTH THE SUITE MISSED: 80 and 240 straddled it without "
              "covering it. At 209 each tile gets ~67 columns against a "
              "BOX_WIDTH of 71, and those four columns are the whole "
              "caption-wrap defect"),
]

#: One column under the derived per-tile minimum, which `test_the_minimum_is_
#: derived_not_chosen` recomputes rather than trusting. Rows are left ample so
#: the failure isolates to WIDTH — the dimension that actually shipped broken.
BELOW_MINIMUM = (74, 24)


# ---- the minimum is derived, not chosen -----------------------------------


def test_the_minimum_is_derived_from_each_panel_and_not_a_fixed_number() -> None:
    """**The real bug.** S009 compared the *window* to a fixed `60×16`.

    A 1920 window split three ways satisfies `60×16` while each tile has far
    less than one panel needs — so the guard could not fire at the size that
    broke, and what rendered was the silently clipped panel §4e forbids.

    The minimum must therefore be a property of the panel's own content. This
    asserts it moves when the content moves; a fixed number would not.
    """
    short = Panel("A", "p", ["  x"])
    long = Panel("A-MUCH-LONGER-TITLE", "p", ["  x"])
    assert long.min_width() > short.min_width(), (
        "min_width ignored the title — it is not derived from content")

    unpinned = Panel("A", "p", ["  x"])
    pinned = Panel("A", "p", ["  x"],
                   pinned=["a very long pinned label indeed   —  (reason)"])
    assert pinned.min_width() > unpinned.min_width(), (
        "min_width ignored the pinned band — §4e's failed rule could be clipped")

    assert Panel("A", "p", ["  x"], pinned=["z"]).min_height() > \
        Panel("A", "p", ["  x"]).min_height(), "min_height ignored the pinned band"


def test_the_pinned_minimum_keeps_the_label_not_the_value() -> None:
    """A pinned row may lose its value to truncation. It may not lose its name —
    `daily limit  — (…)` truncated past `daily limit` is a failed rule rendering
    as punctuation, which is the exact thing §4e's band exists to prevent."""
    p = Panel("T", "prov", ["  row"], pinned=["daily limit  — (no account snapshot)"])
    assert display_width("  daily limit") + 1 <= p.min_width()


def test_the_derived_minimum_for_the_shipped_layout() -> None:
    """Quoted so a change to it is visible in a diff rather than absorbed."""
    need_cols, need_rows, worst = MomentumApp.required(tile_rows())
    assert (need_cols, need_rows) == (75, 11), (
        f"the shipped layout's derived minimum moved to {need_cols}x{need_rows}. "
        "That is not a failure — but BELOW_MINIMUM and the reason strings in "
        "WIDTHS are written against 75x11 and must move with it.")
    assert "WATCHLIST" in worst, "the message must name which tile ran out"
    assert BELOW_MINIMUM[0] == need_cols - 1


# ---- Refusal A — below the per-tile minimum, zero panels ------------------


def test_refusal_a_below_the_per_tile_minimum_no_panel_renders() -> None:
    """**Refusal A. This is the case that shipped broken.**

    S009a 1c: reduced to two rows, only the bottom tile row rendered and no
    `window too small` appeared. §4e's rule is *render the stated message and
    zero panels — never a silently clipped one*, and what shipped was exactly
    the silently clipped case.
    """
    async def go():
        a = app()
        async with a.run_test(size=BELOW_MINIMUM) as pilot:
            await pilot.pause()
            too_small = list(a.query("#too-small"))
            assert too_small, f"no refusal at {BELOW_MINIMUM}"
            assert not list(a.query(Panel)), (
                "a panel rendered into a tile below its minimum — the silently "
                "clipped case §4e forbids")
    asyncio.run(go())


def test_the_guard_measures_the_tile_and_not_the_window() -> None:
    """The regression, stated as the comparison that failed.

    `74×24` clears S009's fixed `60×16` in **both** dimensions, so the old guard
    passed it and let three starved tiles render. The new guard refuses, and the
    message names the tile that ran out rather than only the window.
    """
    cols, rows = BELOW_MINIMUM
    assert cols >= 60 and rows >= 16, (
        "fixture wrong: this size must PASS the old fixed window minimum, "
        "otherwise it does not demonstrate the defect")

    need_cols, need_rows, worst = MomentumApp.required(tile_rows())
    assert cols < need_cols, "the new guard must refuse what the old one passed"
    text = too_small_message(cols, rows, need_cols, need_rows, worst)
    assert "tiles x" in text, "the message does not say what the TILE needed"
    assert "WATCHLIST" in text, "the message does not name the starved tile"
    assert "window too small" in text and "pinned rows do not fit" in text, (
        "the message must keep the ONE meaning S009 §4e narrowed it to")


# ---- Refusal B — the caption is truncated, and the loss renders -----------


def test_refusal_b_a_long_caption_is_truncated_and_the_loss_is_visible() -> None:
    """**Refusal B.** S009a 1a: at 1920 maximized, all six captions wrapped —
    `no ingest / today +`, `not / transmitted +` — and in SIZING and RISK the
    pinned rule overran too, leaving a stray `--` on the next line.

    **That is not cosmetic.** The caption *is* the provenance, and §4 calls a
    panel without a legible update stamp the `[ STALE ]` anti-state. A wrapped
    caption is provenance failing to render as one thing.

    The declared rule: **the caption gives way, the title never does**, and the
    loss renders as an ellipsis. Silent overflow is what shipped.
    """
    long = "ingest 2026-08-12 09:31:04 ET from the archived watchlist v3"
    top = box_top("WATCHLIST", long, 40)
    assert display_width(top) == 40, "the border overran the width it was given"
    assert "WATCHLIST" in top, "the TITLE gave way — the rule says the caption does"
    assert ("…" in top or "..." in top), (
        "the caption was truncated with no marker — a silent loss, which is the "
        "defect, not the fix")
    assert long not in top


def test_no_line_ever_exceeds_the_width_it_was_given() -> None:
    """The invariant, over every panel and every width from the minimum up.

    This is the assertion S009 had no way to make: `_body()` took no width, so
    there was nothing to compare against. Every defect in part 1 is one instance
    of this being false.
    """
    panels = render_panels(empty_record(), Layout.load())
    for width in range(22, 121):
        for name, panel in panels.items():
            if width < panel.min_width():
                continue
            for i, line in enumerate(panel.body(width).splitlines()):
                assert display_width(line) <= width, (
                    f"{name} line {i} is {display_width(line)} wide at width "
                    f"{width}:\n{line!r}")


def test_the_border_is_still_exactly_the_width_at_every_width() -> None:
    """§4d's border rule, generalised off the fixed 71."""
    panels = render_panels(empty_record(), Layout.load())
    for name, panel in panels.items():
        for width in (panel.min_width(), 40, BOX_WIDTH, 200):
            if width < panel.min_width():
                continue
            top = panel.body(width).splitlines()[0]
            assert display_width(top) == width, (
                f"{name} border is {display_width(top)} at width {width}")


def test_fit_charges_the_ellipsis_to_the_budget() -> None:
    """Otherwise the marker that renders the loss causes a new overflow, which
    would be this defect reintroduced by its own fix."""
    for width in range(1, 30):
        assert display_width(fit("x" * 100, width)) <= width


# ---- the viewport is measured too -----------------------------------------


def test_the_viewport_is_measured_against_the_height_it_is_given() -> None:
    """1b's other half. A fixed `viewport=8` is the same defect in the dimension
    nobody looked at: a panel handed six lines rendered nine and let the layout
    clip the surplus with no trace. Measured, the panel reports the shortfall
    itself — §4e's *more below* rather than a silent cut."""
    p = Panel("T", "prov", [f"  row {i}" for i in range(20)], viewport=8)
    tall = p.body(BOX_WIDTH, height=20)
    short = p.body(BOX_WIDTH, height=6)
    assert len(short.splitlines()) <= 6, "the panel overran the height it was given"
    assert len(tall.splitlines()) > len(short.splitlines())
    assert "more ↓" in short, "a clipped panel did not say it was clipped"


# ---- Refusal C — NOT BUILT is a different kind of thing -------------------


def test_refusal_c_not_built_and_data_absent_differ_without_colour() -> None:
    """**Refusal C.** S009a part 3: *"A `NOT BUILT` panel must be visibly a
    different kind of thing from a panel that has data and is refusing."*

    `— (no account snapshot)` means **the machinery exists and the input is
    missing.** `[ NOT BUILT · S010 ]` means **the machinery does not exist.**
    Collapsing them would be the defect this task is fixing, and **no colour may
    carry the distinction** (§4.1) — so the difference must be in the glyphs.
    """
    absent = Cell.absent("no account snapshot").render()
    not_built = Cell.not_built(reason="", slice_id="S010").render()

    assert absent.startswith("—") and "(" in absent, (
        "a data-absent refusal must render as an em-dash and a parenthesised reason")
    assert not_built.startswith("[") and not_built.endswith("]"), (
        "NOT BUILT must render as a bracketed badge")
    assert "—" not in not_built and "(" not in not_built
    assert "[" not in absent
    # Structurally different with every character stripped to its class — which
    # is what "distinguishable without colour" actually means.
    shape = lambda s: "".join("A" if c.isalnum() else c for c in s)[:3]
    assert shape(absent) != shape(not_built)


def test_not_built_names_the_slice_that_will_fill_it() -> None:
    """*"NOT BUILT with the slice that will fill it — `NOT BUILT · S010`."*
    Without it the badge cannot separate *not yet* from *not ever*."""
    assert "S010" in Cell.not_built(reason="", slice_id="S010").render()
    # And an unassigned stage says so rather than inventing a slice number.
    assert "slice not assigned" in Cell.not_built(reason="slice not assigned").render()


# ---- part 3 — the twelve stages -------------------------------------------


#: 018 part 3 renamed the two human rows. They were both `[HUMAN]`, which the
#: value cell already said, so the name column rendered as a gap rather than a
#: stage -- UAT 009 answer D. `select` is after rank and before size; `submit`
#: is after stage and before manage. Both are real stage names, and NEITHER
#: implies a slice, which the value cell continues to make explicit.
TWELVE = ["ingest", "regime", "indicators", "rank", "select", "size",
          "stage", "submit", "manage", "reconcile", "journal", "archive"]


def test_all_twelve_stages_are_declared_in_order() -> None:
    """*"The twelve stages are known and fixed."* A stage absent from the config
    did not render at all, so a stage that exists in the spec and not in code was
    indistinguishable from one that does not exist. Christoph had to ask."""
    assert [s.name for s in Layout.load().stages] == TWELVE


def test_regime_is_not_a_not_built_panel() -> None:
    """*"Regime is not a stage that is coming."* `SPEC.md` §3.2 removes every
    regime layer from the terminal; it is produced by the scheduled task. The
    health panel's pointer is correct and must not be converted."""
    regime = next(s for s in Layout.load().stages if s.name == "regime")
    assert regime.renders == "HEALTH" and not regime.slice
    body = pipeline_panel(Layout.load()).body(BOX_WIDTH)
    regime_row = next(l for l in body.splitlines() if " regime " in l)
    assert "NOT BUILT" not in regime_row, (
        "regime rendered as NOT BUILT — S009a forbids this explicitly")
    assert "HEALTH" in regime_row, "regime must point at the panel that carries it"


def test_a_human_step_does_not_render_as_an_unbuilt_one() -> None:
    """A human step is not a slice and never will be. A stage the system does
    not perform must not render as one it has not performed yet.

    **018 part 3 renamed these from `[HUMAN]` to `select` and `submit`**, so the
    test now keys on the value cell rather than the name — which is the right
    place anyway: the claim is about the STATE, not the label.
    """
    body = pipeline_panel(Layout.load()).body(BOX_WIDTH)
    human = [l for l in body.splitlines() if "your decision" in l]
    assert len(human) == 2, "both human steps must render"
    for row in human:
        assert "NOT BUILT" not in row, (
            "a human step rendered as an unbuilt one. `human: true` is not a "
            "slice that has not arrived; it is work the system never does.")


def test_every_pipeline_row_has_a_name() -> None:
    """**018 part 3.** Rows 5 and 8 rendered with an EMPTY name column.

    Both were declared `name: "[HUMAN]"` while the value cell already said
    *your decision*, so the name read as a gap rather than as a stage — UAT 009
    answer D, and plainly visible in the screenshot before anyone looked for it.

    The check is that every row has a name AND that the name is not a value: a
    cell starting with `[` or `(` is a badge or a reason that has drifted into
    the wrong column.
    """
    body = pipeline_panel(Layout.load()).body(BOX_WIDTH)
    # A stage row is `<n> <name> <value>`. The `12 of 12 · end` summary line has
    # the same leading shape, so it is excluded by its NAME COLUMN being the
    # literal `of` — excluded by what it IS, not by its index, because an index
    # would silently start skipping a real row if one moved.
    matched = [re.match(r"^\s+(\d+)\s+(\S+)", l) for l in body.splitlines()]
    rows = [(m.group(1), m.group(2), m.string) for m in matched
            if m and m.group(2) != "of"]
    assert len(rows) == 12, (
        f"expected 12 stage rows, got {len(rows)}: {[r[1] for r in rows]}")
    for slot, name, line in rows:
        assert not name.startswith(("[", "(")), (
            f"row {slot}'s name column holds a value, not a name: {line!r}")


def test_a_stage_makes_at_most_one_claim_about_its_state() -> None:
    """Two claims render as one badge and the other is silently lost — the same
    shape as every other finding in this task."""
    with pytest.raises(ValueError, match="at most ONE claim"):
        Stage(slot=1, name="x", slice="S010", human=True)
    with pytest.raises(ValueError, match="ordinal"):
        Stage(slot=True, name="x")


def test_the_pipeline_panel_does_not_crowd_out_the_built_ones() -> None:
    """*"Do not let unbuilt stages crowd out built ones."* The compact form
    chosen is **one panel, one row per stage**, taking a normal `1fr` row like
    every other tile — so at a small height it reports what it could not show
    instead of taking the space from SIZING and RISK."""
    p = pipeline_panel(Layout.load())
    assert p.min_height() == 3, (
        "the pipeline panel demands more than one scrolling row of height; at "
        "the 80x24 floor that is taken from the panels that have data")
    assert "of 12" in p.body(BOX_WIDTH, height=6), (
        "a pipeline clipped by a short tile must say how many stages it hid")


# ---- part 2 — the pinned widths -------------------------------------------


def test_every_width_records_why_it_is_here() -> None:
    """*"A snapshot suite that grows by guessing is the list that becomes a
    hiding place."*"""
    for cols, rows, reason in WIDTHS:
        assert len(reason) > 30, f"{cols}x{rows} has no recorded reason"


@pytest.mark.parametrize("size", [(w, h) for w, h, _ in WIDTHS],
                         ids=[f"{w}x{h}" for w, h, _ in WIDTHS])
def test_the_app_renders_panels_at_every_pinned_width(size) -> None:
    async def go():
        a = app()
        async with a.run_test(size=size) as pilot:
            await pilot.pause()
            assert list(a.query(Panel)), f"no panels composed at {size}"
            assert not list(a.query("#too-small")), f"refused at {size}"
    asyncio.run(go())


@pytest.mark.parametrize("size", [(w, h) for w, h, _ in WIDTHS],
                         ids=[f"{w}x{h}" for w, h, _ in WIDTHS])
def test_snapshot_at_each_pinned_width(size) -> None:
    """The render at the width the tile really gets, not at `BOX_WIDTH`.

    S009's snapshots were all taken at the design width, which is precisely why
    they could not see the defect: the thing that broke was the difference
    between the design width and the tile width, and nothing sampled it.
    """
    cols, rows = size
    tile_w = cols // 3 - TILE_PADDING
    panels = render_panels(empty_record(), Layout.load())
    current = "\n\n".join(f"### {n} @ {tile_w}\n{p.body(tile_w)}"
                          for n, p in sorted(panels.items()))
    SNAP_DIR.mkdir(exist_ok=True)
    snap = SNAP_DIR / f"tile-{cols}x{rows}.txt"
    if not snap.exists():
        snap.write_text(current, encoding="utf-8")
        pytest.skip(f"{snap.name} created; re-run to assert against it")
    assert current == snap.read_text(encoding="utf-8"), (
        f"the render at tile width {tile_w} changed. If intended, delete "
        f"{snap.name} and re-run — after reading the diff.")


# ---- 018 part 2: the guard is re-evaluated on every resize ----------------


def _refusal_text(app) -> str:
    """The refusal widget's current text, read back from the widget itself.

    Textual 8 removed `Static.renderable`, so this goes through the render
    pipeline rather than an attribute that no longer exists.
    """
    from rich.text import Text
    w = app.query_one("#too-small")
    return Text.from_markup(str(w.render())).plain if hasattr(w, "render") else ""


def test_shrinking_after_launch_refuses_and_growing_back_restores() -> None:
    """**Refusal A, and the whole of 018 part 2.**

    S009a's guard ran in `compose()`, which fires ONCE. Launched too small it
    refused correctly; **shrunk after launch it never fired**, and the panels
    truncated to `WATCHLIS...` and `(no wat...` instead.

    Christoph's ruling, 2026-08-12: **the terminal refuses.** The rule is *never
    a silently clipped panel*, and a rule that holds only at launch is not the
    rule.

    **Both directions.** A one-way transition would be worse than the behaviour
    it replaces: a terminal that refuses once and never recovers is one you
    restart, and restarting to recover from a resize teaches you not to resize.
    """
    async def go():
        a = app()
        async with a.run_test(size=(209, 54)) as pilot:
            await pilot.pause()
            assert list(a.query(Panel)), "no panels at the working width"
            assert not list(a.query("#too-small"))

            # --- shrink below the per-tile minimum, AFTER launch -------------
            await pilot.resize_terminal(*BELOW_MINIMUM)
            await pilot.pause()
            assert list(a.query("#too-small")), (
                "shrinking after launch did not fire the guard — this is exactly "
                "what shipped broken")
            assert not list(a.query(Panel)), (
                "a panel survived into a window below the minimum: the silently "
                "clipped case §4e forbids")

            # --- grow back above it -----------------------------------------
            await pilot.resize_terminal(209, 54)
            await pilot.pause()
            assert list(a.query(Panel)), (
                "growing back above the minimum did not restore the panels — a "
                "one-way refusal is worse than no refusal")
            assert not list(a.query("#too-small"))
    asyncio.run(go())


def test_the_refusal_message_reflects_the_current_size_not_the_launch_size() -> None:
    """A refusal naming the size the window USED to be is a well-formed value
    answering a different question — the defect this project is named for,
    rendered by the widget whose job is to prevent it."""
    async def go():
        a = app()
        async with a.run_test(size=(209, 54)) as pilot:
            await pilot.pause()
            await pilot.resize_terminal(74, 24)
            await pilot.pause()
            first = _refusal_text(a)
            assert "74x24" in first, f"message does not name the current size: {first!r}"
            assert "209" not in first, f"message still names the launch size: {first!r}"

            # Shrink again WHILE already refusing. The message must move.
            await pilot.resize_terminal(50, 20)
            await pilot.pause()
            second = _refusal_text(a)
            assert "50x20" in second, f"message did not recompute: {second!r}"
            assert "74x24" not in second, (
                f"stale message reused from the previous refusal: {second!r}")
    asyncio.run(go())


def test_refusal_c_slice_not_assigned_stays_reachable_and_differs_from_deferred() -> None:
    """**Refusal C.** 018 part 4 introduced `deferred` for a stage that has been
    RULED ON. **It must not replace `slice not assigned`**, which means nobody
    has decided — a genuine gap.

    *Nobody decided* and *decided to postpone* carry different weight, and the
    screen was making the weaker claim for `manage`. Collapsing them the other
    way would lose the distinction entirely.

    **No colour is involved anywhere.** The distinction is carried by the reason
    text, and deliberately NOT by a new badge word: `[ DEFERRED ]` is not in
    `SPEC.md` §4's vocabulary, and `grammar.py` records that adding one is a spec
    change rather than a code change. Stated as a limit in the done-note — the
    shapes are the same, the words are not.
    """
    unassigned = Cell.not_built(reason="slice not assigned").render()
    deferred = Cell.not_built(reason="deferred - not core, revisit later").render()

    assert "slice not assigned" in unassigned
    assert "deferred" in deferred
    assert unassigned != deferred
    assert "deferred" not in unassigned, (
        "the unassigned state absorbed the deferred wording — a genuine gap "
        "would then read as a decision somebody made")
    # Reachable from a real Stage that declares NO claim at all.
    from live.tui.app import pipeline_panel
    from live.tui.layout import Layout as _L
    gap = Stage(slot=99, name="orphan")
    assert not (gap.slice or gap.built_by or gap.human or gap.deferred or gap.renders)

    # And the shipped layout still renders the deferred one, not the gap one.
    body = pipeline_panel(_L.load()).body(BOX_WIDTH)
    manage = next(l for l in body.splitlines() if " manage " in l)
    assert "deferred" in manage and "slice not assigned" not in manage

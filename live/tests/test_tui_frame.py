"""The frame, the snapshots, and the pinning rule.

**The canonical snapshot is the refusal test**: an empty day record must render
every surface as a NAMED refusal — no crashes, no blanks, no zeros. Any future
change that turns one of those into `0.00` turns this red. That is the project's
core conviction as a runnable thing.

**Note on the snapshot mechanism.** S009 §5 names `pytest-textual-snapshot`.
That package hard-pins `syrupy==4.8.0`, which requires `pytest<9.0.0`, while
this repo declares `pytest>=9.1` and was verified on 9.1.1 — installing it
silently downgraded the test runner. There is no version combination satisfying
both, so the snapshots here are plain text files owned by this suite and the
three widths are driven through Textual's own `run_test(size=...)`. The
behaviour §5 asks for is preserved; only the plugin is not.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from live.tui.app import (BOX_WIDTH, MomentumApp, Panel, display_width,
                          render_panels, too_small_message)
from live.tui.day_record import Attached, DayRecord, Health, empty_record
from live.tui.grammar import Cell
from live.tui.layout import Layout

SNAP_DIR = Path(__file__).parent / "snapshots"

#: §5 — three widths. A layout correct at 120 columns and broken at 240 fails
#: silently on the machine actually used.
WIDTHS = [(80, 24), (120, 40), (240, 70)]


def panels(record: DayRecord | None = None) -> dict[str, Panel]:
    return render_panels(record if record is not None else empty_record(), Layout.load())


# ---- the canonical refusal snapshot ---------------------------------------


def test_empty_record_renders_every_panel_as_a_named_refusal() -> None:
    """**Refusal A — this slice IS the refusal test.**"""
    for name, panel in panels().items():
        body = panel._body()
        assert body.strip(), f"{name} rendered blank"
        assert "0.00" not in body, f"{name} rendered a zero for absent data"
        # Every panel must carry at least one parenthesised reason or a named
        # badge. A refusal without a reason is a blank with extra steps.
        assert ("(" in body and ")" in body) or "[ NOT BUILT ]" in body, (
            f"{name} refuses without naming a reason:\n{body}")


def test_the_canonical_snapshot_is_stable() -> None:
    """Text snapshot of the pure render. Regenerate deliberately, never
    casually — a snapshot updated without reading the diff is not a test."""
    SNAP_DIR.mkdir(exist_ok=True)
    snap = SNAP_DIR / "empty-record.txt"
    current = "\n\n".join(f"### {n}\n{p._body()}" for n, p in sorted(panels().items()))
    if not snap.exists():
        snap.write_text(current, encoding="utf-8")
        pytest.skip("canonical snapshot created; re-run to assert against it")
    assert current == snap.read_text(encoding="utf-8"), (
        "the empty-record render changed.\nIf this was intended, delete "
        f"{snap.relative_to(Path(__file__).parents[2])} and re-run to regenerate — "
        "after reading the diff.")


# ---- chrome ---------------------------------------------------------------


def test_every_border_is_exactly_the_fixed_width() -> None:
    """§4d — the mockups were 69–71 chars against a 71-char border: invisible in
    HTML, visibly broken in a console. Ambiguous-width `·` and `—` are counted."""
    for name, panel in panels().items():
        top = panel._body().splitlines()[0]
        assert display_width(top) == BOX_WIDTH, (
            f"{name} border is {display_width(top)} wide, expected {BOX_WIDTH}")


def test_every_panel_carries_provenance_on_its_top_border() -> None:
    """§4d — *a live panel with no update stamp is the `[ STALE ]` anti-state*."""
    for name, panel in panels().items():
        top = panel._body().splitlines()[0]
        assert panel.provenance and panel.provenance in top, (
            f"{name} has no provenance on its border")


# ---- §4e, the pinning rule ------------------------------------------------


def test_more_below_and_nothing_more_do_not_render_identically() -> None:
    """**The sixth instance of a correct warning nobody was instructed to read.**

    A limit breach at row 19 of a 12-row viewport must not look like no breach.
    """
    short = Panel("T", "p", [f"  row {i}" for i in range(3)], viewport=8)
    long = Panel("T", "p", [f"  row {i}" for i in range(30)], viewport=8)
    assert "end" in short._body()
    assert "more" in long._body()
    assert short._body() != long._body()
    assert "+22 more" in long._body()


def test_a_failed_rule_stays_visible_when_the_panel_is_scrolled_past_it() -> None:
    """**Refusal C.** Without this test the pinning rule is prose.

    The failed rule sits at row 19 of a 30-row panel with an 8-row viewport —
    scrolled far out of view — and must still render, via the pinned band.
    """
    rows = [f"  row {i}" for i in range(30)]
    rows[19] = "  RULE FAILED — stop width exceeds ceiling"
    p = Panel("RISK", "not transmitted", rows, viewport=8,
              pinned=["RULE FAILED — stop width exceeds ceiling"])
    body = p._body()
    assert "row 19" not in body, "fixture wrong: the row should be below the fold"
    assert "RULE FAILED — stop width exceeds ceiling" in body, (
        "a failed rule scrolled out of the viewport vanished — the pinned band "
        "is not working")


def test_pinned_band_is_separated_from_the_scrolling_rows() -> None:
    p = Panel("T", "p", ["  a", "  b"], pinned=["limit 1.0R"])
    lines = p._body().splitlines()
    assert lines[-1].strip() == "limit 1.0R"
    assert set(lines[-2].strip()) <= {"-", "─"}, "no rule separating pinned band"


# ---- §4f, display is not storage ------------------------------------------


def test_a_hidden_component_still_computes(tmp_path: Path) -> None:
    """**Refusal D.** Otherwise only visible components accumulate evidence and
    the inference is circular — tenet 7."""
    cfg = tmp_path / "layout.yaml"
    cfg.write_text(
        "components:\n"
        "  - {id: watchlist, slot: 1, visible: true,  reason: ''}\n"
        "  - {id: tape,      slot: 2, visible: false, reason: 'hidden for this test'}\n",
        encoding="utf-8")
    layout = Layout.load(cfg)
    assert [c.id for c in layout.visible_only] == ["watchlist"]
    assert {c.id for c in layout.all} == {"watchlist", "tape"}, (
        "a hidden component fell out of the compute path")
    # The renderer still produces it; only compose() filters by visibility.
    assert "tape" in render_panels(empty_record(), layout)


def test_slot_is_an_ordinal_not_a_boolean() -> None:
    from live.tui.layout import Component
    with pytest.raises(ValueError, match="ordinal"):
        Component(id="x", slot=True, visible=True)


def test_duplicate_slots_are_rejected(tmp_path: Path) -> None:
    cfg = tmp_path / "layout.yaml"
    cfg.write_text("components:\n"
                   "  - {id: a, slot: 1, visible: true, reason: ''}\n"
                   "  - {id: b, slot: 1, visible: true, reason: ''}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate slot"):
        Layout.load(cfg)


def test_the_shipped_layout_loads_and_has_no_hidden_health() -> None:
    """§4g — the health bar is permanently visible."""
    layout = Layout.load()
    ids = {c.id for c in layout.visible_only}
    assert "health" in ids


# ---- §4b/§5, the three widths ---------------------------------------------


@pytest.mark.parametrize("size", WIDTHS, ids=[f"{w}x{h}" for w, h in WIDTHS])
def test_app_boots_on_an_empty_record_at_every_width(size) -> None:
    """It must boot on an EMPTY record at all three widths without crashing.

    Driven with `asyncio.run` rather than a `pytest.mark.asyncio` marker:
    pytest.ini sets `--strict-markers`, and adding `pytest-asyncio` for two
    tests is a dependency this slice does not need.
    """
    async def go():
        app = MomentumApp()
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            assert list(app.query(Panel)), f"no panels composed at {size}"
            assert not list(app.query("#too-small"))
    asyncio.run(go())


def test_a_too_small_window_says_so_rather_than_clipping() -> None:
    """§5 — a stated `window too small`, never a silently clipped panel. And it
    narrows to ONE meaning: the pinned rows do not fit."""
    msg = too_small_message(40, 10, 60, 16)
    assert "window too small" in msg
    assert "pinned rows do not fit" in msg, (
        "the message must narrow to ONE meaning — not 'the layout is awkward'")
    assert "40x10" in msg and "60x16" in msg, "it must say what is too small"

    async def go():
        app = MomentumApp()
        async with app.run_test(size=(40, 10)) as pilot:
            await pilot.pause()
            assert list(app.query("#too-small")), "no refusal widget at 40x10"
            assert not list(app.query(Panel)), "panels rendered into a too-small window"
    asyncio.run(go())


# ---- §4h, colour ----------------------------------------------------------


def test_no_green_and_no_red_outside_the_one_badge() -> None:
    """Green renders nowhere; red-inverse is reserved for
    `[ STOPPED — DAILY LIMIT ]` alone."""
    src = (Path(__file__).parents[1] / "tui" / "app.py").read_text(encoding="utf-8")
    body = "\n".join(l for l in src.splitlines() if not l.strip().startswith(("#", "*")))
    for banned in ("green", "\"red\"", "'red'"):
        assert banned not in body.lower().replace("rendered", ""), (
            f"{banned!r} appears in the frame; §4h forbids it")


def test_polarity_argument_is_deleted_not_conditioned() -> None:
    """§4h — `_state_cell`'s polarity argument is **deleted**. Not defaulted,
    not conditioned: absent.

    Checked against CODE, not prose. The identifier appears legitimately in the
    module docstring recording the rule; an earlier version of this test failed
    on its own explanation, which is the same self-reference trap the `6 of 9`
    and legacy-path checks hit.
    """
    import ast
    src = (Path(__file__).parents[1] / "tui" / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {a.arg for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              for a in n.args.args}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "polarity" not in names, "a polarity argument or attribute exists in the frame"
    assert "_state_cell" not in names

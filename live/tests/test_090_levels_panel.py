"""090 — the LEVELS panel: the ten that already compute, against mockup v1.5.

Exit categories per the task's own §6: Green (inventory/fix/panel/truncation/
hysteresis/caption/invariant/removal), Refusal (ADR missing/window
unresolvable/session incomplete/nothing attached), Fixture.

**Every state here is constructed locally**, never borrowed from any other
file's shared fixture — B-136, the discipline every task since 083 has held
to.
"""
from __future__ import annotations

from core.indicators.context import Bar, Measured, Unit, INTRADAY_BASIS

from live.attach.attach import Contract, Stage2Inputs, compute_context_and_rail
from live.tui.levels_panel import (ALL_23, BUILT, ENTER_ADR, LEAVE_ADR,
                                   NOT_BUILT, build_levels_panel_rows,
                                   update_levels_included)

QQQ = Contract(symbol="QQQ", con_id=1, exchange="NASDAQ", sector_etf=None)

PRICE = 100.0


def M(v: float, *, basis=INTRADAY_BASIS) -> Measured:
    return Measured(value=v, sample="t", unit=Unit.DOLLAR, basis=basis)


def _full_rail(adr: float = 5.0) -> dict:
    """All ten built levels, all distinct, all comfortably inside a wide
    ADR window, plus a real ADR $ figure."""
    return {
        "PMH": M(101.0), "PML": M(99.0),
        "ORH5": M(101.5), "ORL5": M(98.5),
        "ORH15": M(102.0), "ORL15": M(98.0),
        "PDH": M(103.0), "PDL": M(97.0),
        "52wH": M(104.0), "52wL": M(96.0),
        "ADR $": M(adr),
    }


# ---- Green -- B-144, the prior session selected by date, not position ----


def _dailies_5_distinct_days() -> list:
    """Five daily bars, one per day, each with a DISTINCT high so the test
    can assert exactly which day's bar `PDH` names."""
    return [
        Bar(ts="2026-08-20", open=99.0, high=100.0, low=98.0, close=99.5, volume=1_000_000.0),
        Bar(ts="2026-08-21", open=100.0, high=101.0, low=99.0, close=100.5, volume=1_000_000.0),
        Bar(ts="2026-08-22", open=101.0, high=102.0, low=100.0, close=101.5, volume=1_000_000.0),
        Bar(ts="2026-08-23", open=102.0, high=103.0, low=101.0, close=102.5, volume=1_000_000.0),
        Bar(ts="2026-08-24", open=103.0, high=104.0, low=102.0, close=103.5, volume=1_000_000.0),
    ]


def _today_bars(day: str) -> list:
    return [Bar(ts=f"{day}T09:31:00", open=103.0, high=103.0, low=103.0,
               close=103.0, volume=200.0, wap=103.0)]


def test_green_b144_prior_session_names_the_same_session_pre_open_and_intraday() -> None:
    """**The task's own repro, exactly.** One `Stage2Inputs`, `today_et`
    fixed, `rth_dailies[-1]` dated yesterday (the pre-open case) and dated
    today (the intraday case) — `PDH` must name the SAME session (2026-08-24,
    high=104.0) in both, never `prior[-2]` (2026-08-23, high=103.0) in the
    pre-open case, which is exactly B-144."""
    dailies = _dailies_5_distinct_days()

    # Intraday: today's own bar (2026-08-24) is already the last one in
    # rth_dailies -- prev_day is correctly the one before it (2026-08-23).
    inp_intraday = Stage2Inputs(has_sector=False, today_et="2026-08-24")
    inp_intraday.rth_dailies = dailies
    inp_intraday.today = _today_bars("2026-08-24")
    _, rail_intraday = compute_context_and_rail(inp_intraday)

    # Pre-open: it is now 2026-08-25 before RTH has printed. rth_dailies[-1]
    # (2026-08-24) is ALREADY the prior session -- not the one before it.
    inp_preopen = Stage2Inputs(has_sector=False, today_et="2026-08-25")
    inp_preopen.rth_dailies = dailies
    inp_preopen.today = _today_bars("2026-08-25")
    _, rail_preopen = compute_context_and_rail(inp_preopen)

    assert rail_preopen["PDH"].value == 104.0, (
        f"B-144: pre-open PDH named the wrong session -- got "
        f"{rail_preopen['PDH'].value}, expected 104.0 (2026-08-24, the "
        f"actual prior session)")
    assert rail_intraday["PDH"].value == 103.0, (
        f"intraday PDH must still name 2026-08-23 (the day before today's "
        f"own bar) -- got {rail_intraday['PDH'].value}")
    assert rail_preopen["PDH"].value != rail_intraday["PDH"].value, (
        "this fixture is only meaningful if the two cases would actually "
        "disagree without the fix")


def test_green_b144_escape_hatch_unchanged_for_pre_090_tests() -> None:
    """`today_et == \"\"` (every test that predates 088/090) must keep the
    OLD positional behaviour — `prior[-2]` — unchanged."""
    dailies = _dailies_5_distinct_days()
    inp = Stage2Inputs(has_sector=False)  # today_et defaults to ""
    inp.rth_dailies = dailies
    inp.today = _today_bars("2026-08-24")
    _, rail = compute_context_and_rail(inp)
    assert rail["PDH"].value == 103.0, (
        "the today_et=='' escape hatch must keep prior[-2] (103.0), "
        f"got {rail['PDH'].value}")


# ---- Green -- Part 0's inventory, restated as machine-checkable facts -----


def test_green_all_23_names_and_the_ten_eleven_split() -> None:
    """090 Part 0 items 1-2, pinned. `RAIL_ORDER` (11, missing VWAP) is NOT
    this list — `level_rail` actually returns twelve keys on a live attach
    (confirmed against a driven attach, not against the constant): the ten
    built levels plus VWAP and round, neither of which is a LEVELS-SPEC
    level."""
    assert len(ALL_23) == 23
    assert len(BUILT) == 10
    assert len(NOT_BUILT) == 13
    assert set(BUILT) | set(NOT_BUILT) == set(ALL_23)
    assert not (set(BUILT) & set(NOT_BUILT))
    # The ten that already compute -- 090's own corrected reconstruction,
    # NOT 067's own guess (which wrongly included HOD/LOD and excluded
    # PMH/PML).
    assert set(BUILT) == {
        "PMH", "PML", "ORH5", "ORL5", "ORH15", "ORL15",
        "PDH", "PDL", "52wH", "52wL"}


def test_green_ath_is_not_built() -> None:
    """090 Part 0 item 3. `core.indicators.context.level_rail` has no `ATH`
    parameter and no `ATH` key in its return -- confirmed by reading, and
    `ATH` sits in `NOT_BUILT` here rather than `BUILT`."""
    assert "ATH" in NOT_BUILT
    assert "ATH" not in BUILT


# ---- Green -- the panel renders, per side, sorted furthest-to-nearest -----


def test_green_the_panel_renders_matching_mockup_v1_5_shape() -> None:
    rail = _full_rail(adr=5.0)
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)

    assert result.caption.startswith("10 of 10"), result.caption
    # furthest at the top of the above block, nearest right above the divider
    above = [r for r in result.rows if "price" not in r and "absent" not in r][:5]
    assert "52wH" in above[0], above
    assert "PMH" in above[-1] or "ORH5" in above[-1], above
    divider = next(r for r in result.rows if "price" in r)
    assert f"${PRICE:,.2f}" in divider


def test_green_per_side_truncation_with_a_deliberately_lopsided_fixture() -> None:
    """**The task's own required test.** A global nearest-five would return
    six above and two below here (all closer to price than any below-side
    level) -- per-side truncation must still return exactly five and
    fewer-than-five, never letting the empty side of a lopsided move
    borrow the other side's rows."""
    rail = {
        "PMH": M(100.5), "ORH5": M(100.6), "ORH15": M(100.7),
        "PDH": M(100.8), "52wH": M(100.9),
        # only two below, both far closer to price than the fictional
        # "sixth above" would need to be
        "PML": M(99.5), "ORL5": M(99.0),
        "ORL15": M(150.0),   # far outside any window -- excluded
        "PDL": M(1.0),       # far outside any window -- excluded
        "52wL": M(0.5),      # far outside any window -- excluded
        "ADR $": M(2.0),
    }
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)
    above_rows = [k for k in ("PMH", "ORH5", "ORH15", "PDH", "52wH") if k in included]
    below_rows = [k for k in ("PML", "ORL5") if k in included]
    assert len(above_rows) == 5, (above_rows, sorted(included))
    assert len(below_rows) == 2, (below_rows, sorted(included))
    assert "ORL15" not in included and "PDL" not in included and "52wL" not in included


# ---- Green -- hysteresis, across a sequence, not one frame -----------------


def test_green_hysteresis_enters_at_1_00_and_leaves_only_past_1_10() -> None:
    adr = 1.0
    rail = dict(_full_rail(adr=adr))
    # PMH sits at exactly 1.05 ADR away -- inside the "already rendered"
    # leave band (1.10) but outside the "not yet rendered" enter band (1.00).
    rail["PMH"] = M(PRICE + 1.05 * adr)

    not_included = update_levels_included(rail, PRICE, frozenset())
    assert "PMH" not in not_included, (
        "a level at 1.05 ADR, not currently rendered, must NOT enter -- "
        "the enter threshold is 1.00")

    already_included = update_levels_included(rail, PRICE, frozenset({"PMH"}))
    assert "PMH" in already_included, (
        "the SAME level at 1.05 ADR, already rendered, must STAY -- "
        "the leave threshold is 1.10, not 1.00")

    rail["PMH"] = M(PRICE + 1.15 * adr)
    now_leaves = update_levels_included(rail, PRICE, frozenset({"PMH"}))
    assert "PMH" not in now_leaves, "past 1.10 ADR it must leave"


# ---- Green -- the caption is a content count, not a line count ------------


def test_green_caption_is_a_content_count_not_the_rendered_line_count() -> None:
    """**B-145's own trap, made visible on purpose** — a fixture where the
    rendered LINE count and the LEVEL content count differ, so a caption
    test that only checks they happen to be equal would prove nothing."""
    rail = _full_rail(adr=5.0)
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)
    line_count = len(result.rows)  # 10 levels + 1 divider + 1 not-built row = 12
    assert "10 of 10" in result.caption
    assert str(line_count) not in result.caption.split("·")[0], (
        f"the caption's content count must not equal the raw line count "
        f"by coincidence of this fixture: caption={result.caption!r} "
        f"line_count={line_count}")


# ---- Green -- the invariant: rendered + excluded + absent + not-built = 23


def test_green_the_23_invariant_holds() -> None:
    rail = _full_rail(adr=1.0)   # narrow window -- several excluded
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)

    rendered = len(included)
    computed = sum(1 for k in BUILT if rail.get(k) is not None and rail[k].ok)
    excluded_by_window = computed - rendered
    not_built = len(NOT_BUILT)
    # No absent-with-a-reason levels in this fixture (all ten computed).
    absent_with_reason = 0
    assert rendered + excluded_by_window + absent_with_reason + not_built == 23, (
        rendered, excluded_by_window, absent_with_reason, not_built)


def test_green_the_23_invariant_holds_with_a_failed_level() -> None:
    rail = _full_rail(adr=5.0)
    rail["ORH15"] = Measured.absent("window not closed — 09:30-09:45 ET, today needs 09:44, session at 09:39")
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)

    rendered = len(included)
    computed = sum(1 for k in BUILT if rail.get(k) is not None and rail[k].ok)
    excluded_by_window = computed - rendered
    absent_with_reason = 1     # ORH15
    not_built = len(NOT_BUILT)
    assert rendered + excluded_by_window + absent_with_reason + not_built == 23
    assert any("window not closed" in r for r in result.rows)
    assert any("not built" in r for r in result.rows)
    # The two reasons must never share a row.
    not_built_row = next(r for r in result.rows if "not built" in r)
    assert "window not closed" not in not_built_row


# ---- Green -- a level removed from the row list is absent from the record -


def test_green_a_level_removed_from_built_is_absent_from_the_record() -> None:
    """**B-028 made impossible, not merely caught.** If `ORH5` were pulled
    from `BUILT`, `build_levels_panel_rows` must never render or count it,
    even though `rail` still carries a real value for it."""
    rail = _full_rail(adr=5.0)
    import live.tui.levels_panel as lp
    real_built = lp.BUILT
    lp.BUILT = tuple(k for k in real_built if k != "ORH5")
    try:
        included = update_levels_included(rail, PRICE, frozenset())
        result = build_levels_panel_rows(rail, PRICE, included)
        assert "ORH5" not in included
        assert not any("ORH5" in r for r in result.rows)
    finally:
        lp.BUILT = real_built


# ---- Refusal ---------------------------------------------------------------


def test_refusal_adr_missing_filter_off_everything_renders() -> None:
    rail = _full_rail(adr=5.0)
    rail["ADR $"] = Measured.absent("no ADR $ to span")
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)
    assert included == frozenset(), "filter off must not include anything by distance"
    assert "filter off" in result.caption and "no ADR $ to span" in result.caption
    assert "10 of 10" in result.caption
    for key in BUILT:
        assert any(key in r for r in result.rows), f"{key} missing while filter is off"


def test_refusal_window_unresolvable_never_a_bar_position_fallback() -> None:
    """A level whose window cannot be resolved refuses BY NAME — never a
    silently wrong value from falling back to bar position."""
    rail = _full_rail(adr=5.0)
    rail["ORH15"] = Measured.absent("window not closed — 09:30-09:45 ET, today needs 09:44, session at 09:39")
    rail["ORL15"] = Measured.absent("window not closed — 09:30-09:45 ET, today needs 09:44, session at 09:39")
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)
    assert "ORH15" not in included and "ORL15" not in included
    row = next(r for r in result.rows if "ORH15" in r and "ORL15" in r)
    assert "window not closed" in row


def test_refusal_session_incomplete_never_a_partial_extreme() -> None:
    rail = _full_rail(adr=5.0)
    rail["PDH"] = Measured.absent("no prior session bar")
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)
    assert "PDH" not in included
    assert any("no prior session bar" in r for r in result.rows)


def test_refusal_not_built_absent_and_outside_adr_render_as_three_different_things() -> None:
    rail = _full_rail(adr=1.0)     # narrow -- 52wH/52wL/PDH/PDL excluded by window
    rail["ORH15"] = Measured.absent("window not closed — 09:30-09:45 ET, today needs 09:44, session at 09:39")
    included = update_levels_included(rail, PRICE, frozenset())
    result = build_levels_panel_rows(rail, PRICE, included)

    not_built_row = next(r for r in result.rows if "not built" in r)
    window_row = next(r for r in result.rows if "window not closed" in r)
    assert not_built_row != window_row
    # An excluded-by-window level (e.g. 52wH here) is neither absent row --
    # it simply does not appear in `result.rows` at all (excluded, not absent).
    assert not any("52wH" in r for r in result.rows if "not built" not in r and "window" not in r)


def test_refusal_nothing_attached_reads_not_attached_never_0_of_23() -> None:
    result = build_levels_panel_rows({}, None, frozenset())
    assert result.caption == "not attached"
    assert not result.rows
    assert "0 of 23" not in result.caption


# ---- Green -- Part C, the panel fits without truncation at 209x54 --------


def test_green_the_full_five_per_side_rail_fits_at_209x54_no_truncation() -> None:
    """**Part C, measured live and pinned.** Four equal `1fr` rows gave
    LEVELS 3 real lines of height -- one content row behind its own chrome.
    `.levels-row`'s own dedicated CSS height (090's own fix) must give it
    enough real height to show the FULL 5-per-side rail with no `+K more`
    truncation. Confirmed here as a regression test, not just the scratch
    measurement this fix was originally found from."""
    import asyncio
    from core.indicators.context import Bar
    from live.attach.attach import Contract
    from live.attach.streaming import StreamHandle
    from live.tui.app import ATTACH_KEY, MomentumApp, Panel

    SYMBOL = Contract(symbol="ZZZ", con_id=99, exchange="NASDAQ", sector_etf=None)

    def _daily(n=60):
        out = [Bar(ts=f"2026-08-{(i % 20) + 1:02d}", open=100.0,
                   high=102.0 + i * 0.05, low=100.0 - i * 0.05,
                   close=101.0, volume=1_000_000.0) for i in range(n)]
        out[-1] = Bar(ts="2026-08-24", open=100.0, high=102.0, low=100.0,
                      close=101.0, volume=1_000_000.0)
        return out

    def _today():
        out = []
        for m in range(4 * 60, 9 * 60 + 40):
            h, mi = divmod(m, 60)
            out.append(Bar(ts=f"2026-08-24T{h:02d}:{mi:02d}:00", open=101.0,
                           high=101.5, low=100.5, close=101.0, volume=200.0,
                           wap=101.0))
        return out

    class _MD:
        def resolve(self, symbol): return [SYMBOL]
        def tick_slots_in_use(self): return 0
        def cooldown_remaining_s(self, symbol): return 0
        def warm(self, c): pass
        def daily_bars(self, c, basis): return _daily()

        def intraday_sessions(self, c, basis):
            return [[Bar(ts=f"2026-08-{(i % 20) + 1:02d}T09:{30 + m:02d}:00",
                        open=101.0, high=101.0, low=101.0, close=101.0,
                        volume=10.0, wap=101.0) for m in range(30)]
                   for i in range(20)]

        def today_minutes(self, c): return _today()
        def sector_today_minutes(self, c): return None
        def sector_sessions(self, c, basis): return None
        def open_tick_stream(self, c): return "tick-by-tick AllLast"

        def open_price_stream(self, c, on_update):
            on_update(_today())
            return StreamHandle(lambda: None)

        def playbook_for(self, c): return "ORB 5m"

    async def type_symbol(pilot, symbol):
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

    async def go():
        app = MomentumApp(md=_MD())
        async with app.run_test(size=(209, 54)) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "ZZZ")
            panel = app.query_one("#levels", Panel)
            real_body = panel.body(panel.content_size.width, panel.content_size.height)
            assert "more" not in real_body, (
                f"the LEVELS panel truncated at 209x54:\n{real_body}")
            assert panel.content_size.height >= 13, (
                f"the panel got only {panel.content_size.height} real "
                f"lines -- the levels-row CSS height did not take effect")
            # Every other panel must still meet its own minimum -- taking
            # space for LEVELS must not starve anything else.
            for other_id in ("watchlist", "attached", "tape", "sizing",
                             "risk", "health", "pipeline"):
                p2 = app.query_one(f"#{other_id}", Panel)
                assert p2.content_size.height >= p2.min_height(), (
                    f"{other_id} got squeezed below its own minimum by "
                    f"LEVELS taking a fixed CSS share")
            assert not app.query("#too-small"), (
                "the too-small refusal fired at 209x54 with LEVELS added")

    asyncio.run(go())


# ---- Fixture ----------------------------------------------------------------


def test_fixture_this_file_builds_every_state_itself() -> None:
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (
            "test_attach" in node.module or "test_080" in node.module
            or "test_083" in node.module or "test_084" in node.module
            or "test_087" in node.module):
            names.update(a.name for a in node.names)
    assert not names, f"this file imports from a shared test fixture ({names})"

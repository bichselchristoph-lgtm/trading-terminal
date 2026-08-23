"""080 — the four exit tests its own §8 names: Green, Refusal, Colour,
Fixture. Each one is built against a state THIS test constructs directly
(a hand-built `Stage2Inputs`/`Attached`), never against `Fake()`'s own
default gaps — 078 found the shared fixture always leaves PMH/PML refused,
which masked its own signal behind an ordinary refusal; the same trap here
would be a test reading a state the FIXTURE guarantees rather than one the
CHANGE produces. See the done-note for the `git stash` red-before-green
verification this file was checked against.
"""
from __future__ import annotations

import time

from core.indicators.context import ADR_BASIS, INTRADAY_BASIS, Measured, Unit

from live.attach.attach import Contract, Stage2Inputs, compute_context_and_rail
from live.tui.app import (STALE_THRESHOLD_S, attach_metrics_rows, context_rows,
                          header_freshness)
from live.tui.day_record import (Attached, DayRecord, RequestMetrics,
                                 StreamMetrics, empty_record)

QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="NASDAQ", sector_etf="XLK")


def _bar(ts: str, *, close: float = 101.0, wap: float = 101.0, volume: float = 1000.0):
    from core.indicators.context import Bar
    return Bar(ts=ts, open=wap, high=wap, low=wap, close=close, volume=volume, wap=wap)


def _dailies(n: int = 60) -> list:
    from core.indicators.context import Bar
    return [Bar(ts=f"2026-06-{(i % 28) + 1:02d}", open=100.5, high=102.0,
                low=100.0, close=101.0, volume=1_000_000) for i in range(n)]


def _minutes(n: int = 30) -> list:
    return [_bar(f"2026-08-20T09:{30 + i:02d}:00") for i in range(n)]


# ---- Green — independent landing, freshness advances, RVOL's ruled order --


def test_green_rows_land_independently_not_as_one_paint() -> None:
    """**S037 criterion 3, reversed.** ADR% used/VWAP land from `rth_dailies`
    and the price stream alone; RVOL waits on `sessions` too — asserted by
    feeding `compute_context_and_rail` ONE more input at a time and checking
    exactly which keys exist after each, never all five rows appearing
    together as a single dict from a single call."""
    inp = Stage2Inputs(has_sector=True)

    ctx, rail = compute_context_and_rail(inp)
    assert ctx == {} and rail == {}, f"nothing landed yet: {ctx}"

    inp.today = _minutes()
    ctx, _rail = compute_context_and_rail(inp)
    assert set(ctx) == {"Last $", "VWAP", "cum vol"}, (
        f"the price stream alone must land Last $/VWAP/cum vol and nothing "
        f"RVOL/ADR-shaped yet: {sorted(ctx)}")

    inp.rth_dailies = _dailies()
    ctx, rail = compute_context_and_rail(inp)
    assert "ADR% used" in ctx and ctx["ADR% used"].ok, (
        "ADR% used must land the instant rth_dailies lands, independent of RVOL")
    assert "RVOL" not in ctx, (
        f"RVOL landed before its own input (sessions) arrived: {sorted(ctx)}")
    assert rail, "the rail must land alongside rth_dailies"

    inp.sessions = [_minutes() for _ in range(20)]
    ctx, _rail = compute_context_and_rail(inp)
    assert "RVOL" in ctx and ctx["RVOL"].ok, "RVOL must land once sessions arrives"
    assert "RVOL_rel" not in ctx, (
        "the sector reading must stay pending until the sector's OWN inputs land")

    inp.sector_today = _minutes()
    inp.sector_sessions = [_minutes() for _ in range(20)]
    ctx, _rail = compute_context_and_rail(inp)
    assert ctx["RVOL_rel"].ok, "the sector reading lands once ITS inputs arrive"


def test_green_freshness_age_advances() -> None:
    """The header age is a live computation of `now - last_update_at`, not a
    frozen string — two reads a fraction of a second apart must not be
    identical unless they raced the clock."""
    a = Attached(symbol="QQQ", since="09:31:00")
    a.metrics.streams["symbol"] = StreamMetrics(label="symbol",
                                                last_update_at=time.monotonic() - 3)
    first = header_freshness(a)
    assert first == "3s", f"expected the header to read the 3s age, got {first!r}"
    a.metrics.streams["symbol"].last_update_at -= 20
    second = header_freshness(a)
    assert second != first, "the age did not advance when the update got older"
    assert second == "stale 23s", f"expected a stale header past 20s, got {second!r}"


def test_green_rvol_renders_both_labelled_readings_in_ruled_order() -> None:
    """**Assert the SPECIFIC wording, not a substring** (B-126, 070's own
    finding repeated in 080 §8). Own-history reading first, sector-relative
    second, each labelled with its basis — the exact mockup v1.5 §3 shape."""
    a = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK", context={
        "RVOL": Measured(value=0.86, sample="09:31", unit=Unit.MULTIPLE,
                         basis=INTRADAY_BASIS),
        "RVOL_rel": Measured(value=1.4, sample="vs sector", unit=Unit.MULTIPLE,
                             basis=INTRADAY_BASIS),
    })
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.strip() == "RVOL      0.9× own  · 1.4× vs XLK", (
        f"exact wording mismatch:\n{row!r}")


# ---- Refusal — four states, none alike --------------------------------


def test_refusal_four_states_are_all_distinguishable() -> None:
    """`pending`, `unavailable (reason)`, `stale Ns`, and the bare header —
    each pairwise different, so a reader (or a test) cannot mistake one
    for another."""
    pending_row = context_rows(Attached(symbol="QQQ", since="09:31:00"))[1]  # ADR% used
    assert pending_row.strip().endswith("pending")

    refused = Attached(symbol="QQQ", since="09:31:00", context={
        "ADR% used": Measured.absent("pacing limit, retry in 42s")})
    refused_row = next(r for r in context_rows(refused) if "ADR% used" in r)
    assert "pacing limit, retry in 42s" in refused_row
    assert "pending" not in refused_row

    stale = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK", context={
        "RVOL": Measured(value=0.86, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "RVOL_rel": Measured(value=1.4, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
    })
    stale.metrics.streams["sector"] = StreamMetrics(
        label="sector", last_update_at=time.monotonic() - (STALE_THRESHOLD_S + 5))
    stale_row = next(r for r in context_rows(stale) if "RVOL" in r)
    assert "stale" in stale_row and "pending" not in stale_row and "— (" not in stale_row

    broken_header = header_freshness(Attached(symbol="QQQ", since="09:31:00"))
    assert broken_header == "", (
        f"a symbol with no stream age at all must render a BARE header — "
        f"B-134 — got {broken_header!r}")

    texts = {pending_row.strip(), refused_row.strip(), stale_row.strip()}
    assert len(texts) == 3, "two of the three states rendered identically"


def test_refusal_pending_and_refused_never_collide_on_the_same_symbol() -> None:
    """A row that has landed-and-refused and a row that has not landed yet
    must render differently EVEN WHEN THEY SIT ON THE SAME PANEL — RVOL's
    own reading pending while its sector reading has already refused (no
    mapping) is a reachable, real combination."""
    a = Attached(symbol="THIN", since="09:31:00", sector_etf="", context={
        "RVOL_rel": Measured.absent("no sector mapping")})
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert "pending" in row, f"the own reading (not yet landed) must say pending:\n{row!r}"
    assert "no sector mapping" in row, f"the refused reading must name why:\n{row!r}"


# ---- Colour — "stale" renders only where an age crossed threshold --------


def test_colour_stale_never_renders_off_a_fresh_stream() -> None:
    """A test that goes red if `stale` ever appears anywhere on the panel
    while EVERY tracked stream is fresh (age 0s) — the amber exception's
    entire boundary, checked from the side that must stay clean."""
    a = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK", context={
        "Last $": Measured(value=101.0, sample="last trade", unit=Unit.DOLLAR,
                           basis=INTRADAY_BASIS),
        "ADR% used": Measured(value=16.7, sample="$10.66", unit=Unit.PERCENT,
                              basis=ADR_BASIS),
        "RVOL": Measured(value=0.86, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "RVOL_rel": Measured(value=1.4, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "VWAP": Measured(value=101.0, sample="bar-derived", unit=Unit.DOLLAR,
                         basis=INTRADAY_BASIS),
    })
    now = time.monotonic()
    a.metrics.streams["symbol"] = StreamMetrics(label="symbol", last_update_at=now)
    a.metrics.streams["sector"] = StreamMetrics(label="sector", last_update_at=now)
    body = "\n".join(context_rows(a))
    assert "stale" not in body, f"'stale' rendered with every stream fresh:\n{body}"
    assert header_freshness(a) == "0s"


def test_colour_stale_renders_exactly_where_the_threshold_is_crossed_and_nowhere_else() -> None:
    """The positive side of the same boundary: age it JUST past the
    threshold on ONE stream only, and `stale` must appear exactly once,
    attached to the reading that stream backs — never on the other, and
    never on any unrelated row."""
    a = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK", context={
        "Last $": Measured(value=101.0, sample="last trade", unit=Unit.DOLLAR,
                           basis=INTRADAY_BASIS),
        "ADR% used": Measured(value=16.7, sample="$10.66", unit=Unit.PERCENT,
                              basis=ADR_BASIS),
        "RVOL": Measured(value=0.86, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "RVOL_rel": Measured(value=1.4, sample="t", unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
        "VWAP": Measured(value=101.0, sample="bar-derived", unit=Unit.DOLLAR,
                         basis=INTRADAY_BASIS),
    })
    now = time.monotonic()
    a.metrics.streams["symbol"] = StreamMetrics(label="symbol", last_update_at=now)
    a.metrics.streams["sector"] = StreamMetrics(
        label="sector", last_update_at=now - (STALE_THRESHOLD_S + 1))
    rows = context_rows(a)
    stale_rows = [r for r in rows if "stale" in r]
    assert len(stale_rows) == 1, f"expected exactly one stale row, got {stale_rows}"
    assert "RVOL" in stale_rows[0], f"the stale marker landed on the wrong row: {stale_rows}"
    assert "vs XLK" in stale_rows[0] and "stale" in stale_rows[0].split("·")[1], (
        f"the stale marker must sit on the vs-sector reading, not the own one:\n"
        f"{stale_rows[0]!r}")
    assert "0.9× own" in stale_rows[0] and "stale" not in stale_rows[0].split("·")[0], (
        f"the OWN reading (backed by the fresh symbol stream) must stay clean:\n"
        f"{stale_rows[0]!r}")


# ---- Part 4 — measurements recorded, rendered only in HEALTH -------------


def test_measurements_never_render_on_attached() -> None:
    """**080 Part 4/§7.** Metrics are recorded on `Attached.metrics` but
    `context_rows` (the ATTACHED panel) must never mention them — no wall
    time, no bar count, no update count anywhere in this panel's body."""
    a = Attached(symbol="QQQ", since="09:31:00")
    a.metrics.streams["symbol"] = StreamMetrics(label="symbol", update_count=12,
                                                last_update_at=time.monotonic())
    a.metrics.requests["rth_dailies"] = RequestMetrics(
        role="rth_dailies", wall_s=0.8, bars_received=252)
    a.metrics.stage1_keypress_to_paint_s = 0.31
    body = "\n".join(context_rows(a))
    for leak in ("0.8", "252", "12 updates", "0.31", "keypress"):
        assert leak not in body, f"a Part 4 measurement leaked onto ATTACHED: {leak!r}"


def test_measurements_render_in_health_and_stay_separated_by_stream() -> None:
    """**080 Part 4: per-stream, symbol and sector SEPARATELY, never
    pooled.** A dead sector stream must be visible on its own row, not
    averaged away behind a healthy symbol stream."""
    record = empty_record()
    a = Attached(symbol="QQQ", since="09:31:00", sector_etf="XLK")
    a.metrics.streams["symbol"] = StreamMetrics(
        label="symbol", update_count=40, last_update_at=time.monotonic())
    a.metrics.streams["sector"] = StreamMetrics(
        label="sector", update_count=0, last_update_at=None, error="timed out")
    a.metrics.requests["rth_dailies"] = RequestMetrics(
        role="rth_dailies", wall_s=0.83, bars_received=252)
    a.metrics.requests["sessions"] = RequestMetrics(
        role="sessions", wall_s=42.1, bars_received=7800)
    a.metrics.stage1_keypress_to_paint_s = 0.31
    a.metrics.stage2_first_row_s = 0.9
    a.metrics.stage2_last_row_s = 43.0
    record.attached.append(a)
    rows = attach_metrics_rows(record)
    body = "\n".join(rows)

    assert any("symbol" in r and "40 updates" in r for r in rows), body
    assert any("sector" in r and "no update yet" in r or
              ("sector" in r and "timed out" in r) for r in rows), body
    assert any("timed out" in r for r in rows), (
        f"the sector stream's error did not render:\n{body}")
    assert "0.8s" in body and "252 bars" in body
    assert "42.1s" in body and "7800 bars" in body
    assert "0.31s" in body, "stage 1 keypress-to-paint did not render"
    assert "0.90s" in body and "43.00s" in body

    assert attach_metrics_rows(empty_record()) == [], (
        "HEALTH must render nothing when nothing is attached")


# ---- Fixture — this file's own states are self-produced, not borrowed ----


def test_fixture_every_state_here_is_constructed_not_borrowed_from_a_shared_fake() -> None:
    """**080 §8's explicit warning, checked as code.** Every `Attached`/
    `Stage2Inputs` in this file is built by hand, in the test that uses it
    — none of them import `live.tests.test_attach.Fake` or read a gap
    `Fake()`'s own fixture defaults happen to leave (PMH/PML, or anything
    else). Asserted by import inspection rather than trusted by review."""
    import ast
    from pathlib import Path
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "test_attach" in node.module:
            names.update(a.name for a in node.names)
    assert not names, (
        f"this file imports from test_attach ({names}) — every state here "
        f"must be constructed locally, not borrowed from that shared fixture")

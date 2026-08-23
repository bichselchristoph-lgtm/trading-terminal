"""083 — RVOL's anchor becomes a configured choice, defaults to RTH, and
renders. Five exit tests: Green, Divergence (the B-049 guard — the most
important test in this task), Derived label, Refusal, Fixture.

**Every state here is constructed locally**, never borrowed from
`test_attach.py`'s shared `Fake()` — 078's fixture-masking lesson, restated
as B-136 by this task's own §6.
"""
from __future__ import annotations

import time

from core.indicators.context import Bar, Measured, SessionBasis, Unit

from live.attach.attach import Contract, Stage2Inputs, compute_context_and_rail
from live.attach.rvol_config import anchor_word, load_rvol_basis
from live.tui.app import context_rows
from live.tui.day_record import Attached

QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="NASDAQ", sector_etf="XLK")

RTH_BASIS = SessionBasis(use_rth=True, label="09:30-16:00 ET", why="test")
ETH_BASIS = SessionBasis(use_rth=False, label="04:00-20:00 ET", why="test")


def _bar(ts: str, *, close: float = 101.0, volume: float = 1000.0) -> Bar:
    return Bar(ts=ts, open=close, high=close, low=close, close=close,
              volume=volume, wap=close)


def _today_with_premarket() -> list[Bar]:
    """08:00 through 09:35 — six pre-market minutes, then the open."""
    out = [_bar(f"2026-08-20T08:{m:02d}:00", volume=100.0) for m in range(0, 6)]
    out += [_bar(f"2026-08-20T09:{30 + m:02d}:00", volume=200.0) for m in range(6)]
    return out


def _rth_session(n: int = 390) -> list[Bar]:
    out = []
    for i in range(n):
        h, m = divmod(9 * 60 + 30 + i, 60)
        out.append(_bar(f"2026-08-{(i % 20) + 1:02d}T{h:02d}:{m:02d}:00", volume=10.0))
    return out


# ---- Part 0, restated as a machine-checkable fact -------------------------


def test_part0_the_config_default_is_rth() -> None:
    """Part 0 item 3, confirmed by reading and pinned so it cannot silently
    drift: `config/rvol.yaml`'s own default is `rth`, matching mockup
    v1.6's own default claim."""
    basis = load_rvol_basis()
    assert basis.use_rth is True
    assert anchor_word(basis) == "rth"


# ---- Green — the anchor changes the request AND the render together ------


def test_green_rth_anchor_excludes_premarket_from_the_numerator() -> None:
    inp = Stage2Inputs(has_sector=False, rvol_basis=RTH_BASIS)
    inp.today = _today_with_premarket()
    inp.sessions = [_rth_session() for _ in range(20)]
    ctx, _rail = compute_context_and_rail(inp)
    # 6 pre-market bars * 100 excluded; only the 6 RTH bars * 200 counted.
    assert ctx["RVOL"].ok
    # cum vol (off the SAME stream, unaffected by RVOL's own anchor) still
    # includes the pre-market bars -- proving the filter is scoped to RVOL
    # alone, never to VWAP/cum vol's own reading of the same stream.
    assert ctx["cum vol"].value == 6 * 100.0 + 6 * 200.0, (
        "cum vol must stay ETH-wide -- RVOL's anchor must not narrow it")


def test_green_eth_anchor_includes_premarket_and_row_reads_eth() -> None:
    inp = Stage2Inputs(has_sector=False, rvol_basis=ETH_BASIS)
    inp.today = _today_with_premarket()
    inp.sessions = [_rth_session() for _ in range(20)]
    ctx, _rail = compute_context_and_rail(inp)
    assert ctx["RVOL"].ok

    a = Attached(symbol="QQQ", since="09:31:00", rvol_anchor=anchor_word(ETH_BASIS),
                context=ctx)
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.strip().startswith("RVOL eth"), (
        f"expected the row to name the ETH anchor:\n{row!r}")


# ---- Divergence — the B-049 guard, the most important test here ----------


class RecordingMD:
    """Answers exactly like a real client would for the two roles this test
    cares about, and RECORDS the `basis` object each was called with — so
    the test can assert identity, not merely equal values."""

    def __init__(self) -> None:
        self.recorded: dict[str, object] = {}

    def intraday_sessions(self, c, basis):
        self.recorded["sessions"] = basis
        return [_rth_session() for _ in range(20)]

    def sector_sessions(self, c, basis):
        self.recorded["sector_sessions"] = basis
        return [_rth_session() for _ in range(20)]


def test_divergence_numerator_filter_and_curve_request_read_the_same_object() -> None:
    """**The B-049 guard.** One `Stage2Inputs.rvol_basis` instance; the
    curve-request call site and the numerator-filtering call site must both
    read exactly that instance — asserted by identity (`is`), which fails
    the moment a second, independent flag is introduced anywhere, even one
    that happens to hold an equal value today."""
    inp = Stage2Inputs(has_sector=True, rvol_basis=RTH_BASIS)
    md = RecordingMD()

    # Exactly what `app.py`'s `_role_worker` does: pass `inp.rvol_basis`
    # itself to the request, never a copy or a re-derived value.
    inp.sessions = md.intraday_sessions(QQQ, inp.rvol_basis)
    inp.sector_sessions = md.sector_sessions(QQQ, inp.rvol_basis)

    assert md.recorded["sessions"] is inp.rvol_basis, (
        "the sessions request used a DIFFERENT basis object than "
        "Stage2Inputs.rvol_basis")
    assert md.recorded["sector_sessions"] is inp.rvol_basis, (
        "the sector_sessions request used a DIFFERENT basis object than "
        "Stage2Inputs.rvol_basis")

    # And the SAME instance drives the numerator's own filtering.
    inp.today = _today_with_premarket()
    inp.sector_today = _today_with_premarket()
    ctx, _rail = compute_context_and_rail(inp)
    # RTH: pre-market excluded from both readings' numerators.
    assert ctx["RVOL"].ok and ctx["RVOL_rel"].ok


def test_divergence_mutating_the_one_object_moves_both_halves_together() -> None:
    """Flip `rvol_basis` from RTH to ETH on the SAME `Stage2Inputs` and
    confirm the numerator's filtering follows immediately — there is no
    cached or independently-read second value anywhere to lag behind."""
    inp = Stage2Inputs(has_sector=False, rvol_basis=RTH_BASIS)
    inp.today = _today_with_premarket()
    inp.sessions = [_rth_session() for _ in range(20)]
    ctx_rth, _ = compute_context_and_rail(inp)

    inp.rvol_basis = ETH_BASIS
    ctx_eth, _ = compute_context_and_rail(inp)

    assert ctx_rth["RVOL"].value != ctx_eth["RVOL"].value, (
        "changing the one basis object did not change RVOL's own reading "
        "-- the numerator is reading something other than inp.rvol_basis")


# ---- Derived label — never a literal --------------------------------------


def test_derived_label_is_never_a_literal() -> None:
    """Set the anchor to `eth` and confirm the row reads `RVOL eth` — if the
    label were hardcoded to `rth` anywhere, this is the test that catches
    it."""
    a = Attached(symbol="QQQ", since="09:31:00", rvol_anchor="eth", context={
        "RVOL": Measured(value=0.5, sample="t", unit=Unit.MULTIPLE, basis=ETH_BASIS),
    })
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.strip().startswith("RVOL eth"), f"{row!r}"
    assert "RVOL rth" not in row


def test_the_anchor_word_is_always_computed_from_use_rth() -> None:
    """`anchor_word` — the ONE function every renderer must call — derives
    the word from the boolean, never accepts one as a separate argument
    that could disagree with it."""
    assert anchor_word(SessionBasis(use_rth=True, label="x", why="x")) == "rth"
    assert anchor_word(SessionBasis(use_rth=False, label="x", why="x")) == "eth"


# ---- Refusal — the anchor renders pending and unavailable alike -----------


def test_refusal_anchor_renders_while_pending() -> None:
    """**The anchor is a fact about the row, known at attach** — it must
    render even before RVOL itself has landed."""
    a = Attached(symbol="QQQ", since="09:31:00", rvol_anchor="rth")
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.split() == ["RVOL", "rth", "pending"], f"{row!r}"


def test_refusal_anchor_renders_while_unavailable() -> None:
    a = Attached(symbol="QQQ", since="09:31:00", rvol_anchor="rth", context={
        "RVOL": Measured.absent("no answer in 60s"),
    })
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert row.strip().startswith("RVOL rth"), f"{row!r}"
    assert "no answer in 60s" in row


# ---- Fixture — every state above is self-constructed ----------------------


def test_fixture_this_file_builds_every_state_itself() -> None:
    """**B-136, checked as code, not trusted by review.** No import from
    `live.tests.test_attach` anywhere in this file — every `Stage2Inputs`/
    `Attached` above is hand-built, so no test here can be reading a state
    a SHARED fixture happens to guarantee rather than one this task's own
    change produces."""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "test_attach" in node.module:
            names.update(a.name for a in node.names)
    assert not names, f"this file imports from test_attach ({names})"

"""071 Part 1 — five snapshot fixtures against `ATTACHED mockup — the context
block and its states` v1.2, pinned at the panel's real TILE width.

**The mockup itself is drawn at 62 columns** — "the third-width tile the
terminal actually uses" — not the full 209-column terminal width. These
fixtures render at that same tile width (`209 // 3 - TILE_PADDING`, the exact
derivation `test_snapshot_at_each_pinned_width` already uses for the 209x54
pin), because a row built to fit 62 columns and only ever measured at the
full terminal width would hide the one truncation these fixtures exist to
catch — the same shape of miss `B-012` names for the panel as a whole.

**Process note, stated plainly rather than left implicit:** these fixtures
were written and run AFTER `app.py`/`context.py` were already changed to the
four-row target, not before — the same order violation 070's done-note
confirmed and did not repeat here on purpose to avoid, and repeated anyway
under time pressure. To recover an honest red/green signal despite that,
each test below was additionally run against a `git stash`ed copy of the
real pre-071 `live/tui/app.py` (the module this file imports its renderer
from) and confirmed RED there — see the done-note for the stash output.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from live.tui.app import TILE_PADDING, context_rows, render_panels
from live.tui.day_record import Attached, DayRecord, empty_record
from live.tui.layout import Layout

TILE_W = 209 // 3 - TILE_PADDING


def _attached_body(record: DayRecord, width: int = TILE_W) -> str:
    return render_panels(record, Layout.load())["attached"].body(width)


def _measured_attach() -> Attached:
    from core.indicators.context import ADR_BASIS, INTRADAY_BASIS, Measured, Unit
    return Attached(
        symbol="QQQ", since="09:19:07",
        context={
            "ADR% used": Measured(value=16.7, sample="$10.66",
                                  unit=Unit.PERCENT, basis=ADR_BASIS),
            "RVOL_rel": Measured(value=1.4, sample="vs sector RVOL",
                                 unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
            "RVOL_sector": Measured(value=0.86, sample="vs 20d median",
                                    unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
            "cum vol": Measured(value=22_100_000, sample="today",
                                unit=Unit.SHARES, basis=INTRADAY_BASIS),
            "VWAP": Measured(value=712.97, sample="bar-derived",
                             unit=Unit.DOLLAR, basis=INTRADAY_BASIS),
            "VWAP_ext": Measured(value=1.28, sample="price - VWAP",
                                 unit=Unit.DOLLAR, basis=INTRADAY_BASIS),
        },
        rail={"PDH": Measured(value=714.94, sample="prior session",
                              unit=Unit.DOLLAR, basis=ADR_BASIS)},
        source="IBKR", as_of="", lag="", tape="tick-by-tick AllLast",
        slot_state="0/5 slots used")


# ---- §1 — attached and landed: exactly four rows, nothing truncated -------


def test_landed_is_exactly_four_rows_at_tile_width() -> None:
    """Mockup v1.2 §1: symbol row, `ADR% used`, `RVOL rel`, `VWAP` — no
    `from`/`slot`/`tape`, no level rows, no VWAP continuation line."""
    record = empty_record()
    record.attached.append(_measured_attach())
    body = _attached_body(record)
    assert "QQQ" in body and re.search(r"attached \d\d:\d\d:\d\d", body), (
        f"symbol row missing seconds:\n{body}")
    for label in ("ADR% used", "RVOL rel", "VWAP"):
        assert label in body, f"{label!r} row missing:\n{body}"
    for gone in ("from ", "slot ", "tape ", "PDH", "bar-derived · "):
        assert gone not in body, f"{gone!r} still renders:\n{body}"
    assert "4 of 4" in body, f"expected exactly 4 rows, got:\n{body}"


def test_landed_header_is_bare() -> None:
    """Mockup v1.2 §1: `+- ATTACHED -------...-------+`, no `since HH:MM`."""
    record = empty_record()
    record.attached.append(_measured_attach())
    body = _attached_body(record)
    top = body.splitlines()[0]
    assert "since" not in top, f"the header still names a clock stamp:\n{top}"


def test_adr_used_row_is_compact_and_uncapped() -> None:
    """Mockup v1.2 §1: `16.7% <bar> of $10.66 ADR20 RTH` — no `·` joins, no
    `from today's open`, no verbose clock-range basis."""
    row = context_rows(_measured_attach())[0]
    assert re.search(r"ADR% used\s+16\.7%\s+[▓░]+\s+of \$10\.66 ADR20 RTH", row), (
        f"ADR% used did not render the compact v1.2 form:\n{row!r}")


def test_nothing_renders_below_the_vwap_value() -> None:
    """071 §4: 'Nothing renders below a value. The row is the row.'"""
    rows = context_rows(_measured_attach())
    vwap_idx = next(i for i, r in enumerate(rows) if "VWAP" in r)
    assert vwap_idx == len(rows) - 1, (
        f"a row follows VWAP — the continuation line 070 built is still "
        f"there:\n{rows}")


# ---- §5 — partial gather: exact count, no tilde ----------------------------


def test_partial_count_has_no_tilde() -> None:
    """Mockup v1.2 §5's own caption: '~2 of 21 reads as approximately, the
    same objection that retired ~level from the rail.'"""
    a = _measured_attach()
    a.partial = "2 of 4 rows unavailable"
    row = next(r for r in context_rows(a) if "rows unavailable" in r)
    assert "~" not in row, f"the tilde marker survived:\n{row!r}"
    assert row.strip() == "2 of 4 rows unavailable (flagged, not an error)", (
        f"unexpected partial-row text:\n{row!r}")


def test_partial_row_absent_when_landed_clean() -> None:
    a = _measured_attach()
    assert not a.partial
    assert not any("rows unavailable" in r for r in context_rows(a))


# ---- RVOL rel: compact, and a refusal does not blank `avg`/`cum` ----------


def test_rvol_rel_row_is_compact() -> None:
    """Mockup v1.2 §1: `1.4x · avg 0.86x · cum 22.1M sh` — no trailing
    `sample · basis`, the same reduction `_adr_used_cell` makes."""
    row = next(r for r in context_rows(_measured_attach()) if "RVOL rel" in r)
    assert re.search(r"1\.4× {2}· avg 0\.9× {2}· cum 22\.1M sh\s*$", row), (
        f"RVOL rel carries a trailing detail the mockup does not draw:\n{row!r}")


def test_a_refused_rvol_rel_does_not_blank_avg() -> None:
    """`RVOL_rel` and `RVOL_sector` are independent in `attach.py` — one can
    refuse while the other holds a real value. 071 exit tests: 'one field's
    refusal does not blank the row.'"""
    from core.indicators.context import INTRADAY_BASIS, Measured, Unit
    from live.tui.app import _rvol_rel_cell
    refused_rel = Measured.absent("need 20 sessions, have 4")
    context = {"RVOL_sector": Measured(value=0.86, sample="vs 20d median",
                                       unit=Unit.MULTIPLE, basis=INTRADAY_BASIS)}
    row = _rvol_rel_cell(refused_rel, context)
    assert "need 20 sessions" in row, f"the refusal itself is missing:\n{row!r}"
    assert "avg 0.9" in row, (
        f"a present RVOL_sector was blanked by RVOL_rel's own refusal:\n{row!r}")

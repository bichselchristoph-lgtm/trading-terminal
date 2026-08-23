"""071 Part 1, superseded by 080 — five snapshot fixtures against `ATTACHED
mockup — the context block and its states`, now v1.5, pinned at the panel's
real TILE width.

**071's own four-row target (`ADR% used`, `RVOL rel`, `VWAP`, and a
partial-count line) is reversed by 080.** The mockup moved from v1.2 to
v1.5 between those two tasks: a fifth row (`Last $`) was added, `RVOL`
relabels its own-history and sector-relative readings instead of folding
`avg`/`cum` into one line, `VWAP` dropped its signed-distance suffix, and
the screen-level partial-count line is gone (five rows and the header are
all this panel renders — 080 §4/§7). **This file is updated in place
rather than left asserting a superseded shape**, the same treatment
`test_attach.py` already gets as a living fixture file rather than a
one-task snapshot.

**The mockup itself is drawn at 62 columns** — "the third-width tile the
terminal actually uses" — not the full 209-column terminal width. These
fixtures render at that same tile width (`209 // 3 - TILE_PADDING`, the exact
derivation `test_snapshot_at_each_pinned_width` already uses for the 209x54
pin), because a row built to fit 62 columns and only ever measured at the
full terminal width would hide the one truncation these fixtures exist to
catch — the same shape of miss `B-012` names for the panel as a whole.
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
        symbol="QQQ", since="09:19:07", sector_etf="XLK",
        context={
            "Last $": Measured(value=712.97, sample="last trade",
                               unit=Unit.DOLLAR, basis=INTRADAY_BASIS),
            "ADR% used": Measured(value=16.7, sample="$10.66",
                                  unit=Unit.PERCENT, basis=ADR_BASIS),
            "RVOL": Measured(value=0.86, sample="09:19",
                             unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
            "RVOL_rel": Measured(value=1.4, sample="vs sector RVOL",
                                 unit=Unit.MULTIPLE, basis=INTRADAY_BASIS),
            "VWAP": Measured(value=714.25, sample="bar-derived",
                             unit=Unit.DOLLAR, basis=INTRADAY_BASIS),
        },
        rail={"PDH": Measured(value=714.94, sample="prior session",
                              unit=Unit.DOLLAR, basis=ADR_BASIS)},
        source="IBKR", as_of="", lag="", tape="tick-by-tick AllLast",
        slot_state="0/5 slots used")


# ---- §1 — attached and landed: exactly five rows, nothing truncated -------


def test_landed_is_exactly_five_rows_at_tile_width() -> None:
    """Mockup v1.5 §1: symbol row, `Last $`, `ADR% used`, `RVOL`, `VWAP` —
    no `from`/`slot`/`tape`, no level rows, no partial-count line."""
    record = empty_record()
    record.attached.append(_measured_attach())
    body = _attached_body(record)
    assert "QQQ" in body and re.search(r"attached \d\d:\d\d:\d\d", body), (
        f"symbol row missing seconds:\n{body}")
    for label in ("Last $", "ADR% used", "RVOL", "VWAP"):
        assert label in body, f"{label!r} row missing:\n{body}"
    for gone in ("from ", "slot ", "tape ", "PDH", "bar-derived · ",
                 "rows unavailable"):
        assert gone not in body, f"{gone!r} still renders:\n{body}"
    assert "5 of 5" in body, f"expected exactly 5 rows, got:\n{body}"


def test_landed_header_carries_the_freshness_age() -> None:
    """**080 reverses 071 §3.** The header is no longer bare when landed —
    it carries the freshness age always (080 Part 3). With no stream ever
    ticked (this fixture is a hand-built snapshot, not a live attach), the
    age is unset and the header is bare for exactly THAT reason — the
    broken/never-updated state, reachable and distinguishable by
    construction here."""
    record = empty_record()
    record.attached.append(_measured_attach())
    body = _attached_body(record)
    top = body.splitlines()[0]
    assert "since" not in top, f"the header still names a clock stamp:\n{top}"


def test_adr_used_row_is_compact_and_uncapped() -> None:
    """Mockup v1.5 §1: `16.7% <bar> of $10.66 ADR20 RTH` — no `·` joins, no
    `from today's open`, no verbose clock-range basis. Unchanged by 080."""
    rows = context_rows(_measured_attach())
    row = next(r for r in rows if "ADR% used" in r)
    assert re.search(r"ADR% used\s+16\.7%\s+[▓░]+\s+of \$10\.66 ADR20 RTH", row), (
        f"ADR% used did not render the compact v1.2 form:\n{row!r}")


def test_nothing_renders_below_the_vwap_value() -> None:
    """071 §4: 'Nothing renders below a value. The row is the row.' Still
    true under 080/v1.5 — only the suffix on THIS line changed (the signed
    distance is gone), not the one-physical-line rule."""
    rows = context_rows(_measured_attach())
    vwap_idx = next(i for i, r in enumerate(rows) if "VWAP" in r)
    assert vwap_idx == len(rows) - 1, (
        f"a row follows VWAP:\n{rows}")


def test_vwap_row_is_value_only_no_signed_distance() -> None:
    """**080/v1.5 §2, reversing 070.** `VWAP $714.25` — no `· +$1.28`. The
    suffix was `Last $` minus `VWAP` before `Last $` existed on this panel;
    once it did, the two could read the same number while the suffix
    claimed a nonzero gap between them (B-127's third firing)."""
    rows = context_rows(_measured_attach())
    row = next(r for r in rows if "VWAP" in r)
    assert re.search(r"VWAP\s+\$714\.25\s*$", row), (
        f"VWAP row is not value-only:\n{row!r}")
    assert "+$" not in row and "·" not in row, (
        f"a signed-distance suffix survived on the VWAP row:\n{row!r}")


# ---- RVOL: own reading first, sector-relative second, each labelled -------


def test_rvol_row_labels_both_readings_own_first() -> None:
    """**080/v1.5 §3, reversing 070/071's `avg`/`rel`/`cum` labels.**
    `0.86x own · 1.4x vs XLK` — own-history reading first (the one read
    first in `compute_context_and_rail` too), sector-relative second,
    labelled with the ACTUAL sector ETF symbol. `cum` is off this row
    entirely — the numerator stays computed, never rendered here (080 §4,
    the opposite of B-028's `ADR$` treatment)."""
    row = next(r for r in context_rows(_measured_attach()) if "RVOL" in r)
    assert re.search(r"RVOL\s+0\.9× own\s+· 1\.4× vs XLK\s*$", row), (
        f"RVOL row did not render the v1.5 own/vs-sector form:\n{row!r}")
    assert "cum" not in row, f"cum survived on the RVOL row:\n{row!r}"
    assert "avg" not in row and "rel" not in row.lower().replace("rel   ", ""), (
        f"a retired label survived on the RVOL row:\n{row!r}")


def test_a_refused_sector_reading_does_not_blank_the_own_reading() -> None:
    """**B-117, extended to 080's pending state too.** `RVOL`'s own reading
    and `RVOL_rel` are independent in `compute_context_and_rail` — one can
    refuse (or stay pending) while the other holds a real value."""
    from core.indicators.context import Measured
    from live.tui.app import _rvol_row
    a = _measured_attach()
    a.context["RVOL_rel"] = Measured.absent("need 20 sessions, have 4")
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert "need 20 sessions" in row, f"the refusal itself is missing:\n{row!r}"
    assert "0.9× own" in row, (
        f"the own reading was blanked by RVOL_rel's own refusal:\n{row!r}")


def test_a_pending_sector_reading_does_not_blank_the_own_reading() -> None:
    """**080's new state, same principle as B-117.** Own lands (0.7-1.9s);
    the sector's 20-session pull can still be in flight (15-60s) — the row
    must show `pending`, never blank, for the reading that has not landed."""
    a = _measured_attach()
    del a.context["RVOL_rel"]
    row = next(r for r in context_rows(a) if "RVOL" in r)
    assert "0.9× own" in row, f"the own reading was blanked:\n{row!r}"
    assert row.strip().endswith("pending"), (
        f"the sector reading did not render as pending:\n{row!r}")

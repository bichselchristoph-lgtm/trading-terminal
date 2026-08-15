"""044 Part 1 — every linked token has a partner on screen.

**This is the test that stops the link colour drifting into meaning
*important*, which is a verdict wearing a hat.**

`SPEC.md` §4.1 gives every colour a *kind* and forbids colour from carrying a
judgment. §4.1a adds link colour on one argument: **a verdict is a claim about
one thing, a link is a claim about two, and a link cannot be misread as a
judgment because it never appears alone.** Remove the "never appears alone" and
the argument collapses — a lone violet token is just an emphasised token, and
emphasis is a verdict.

So the invariant is not decoration. **It is the entire reason §4.1a is allowed to
exist**, and it is enforced here rather than described.

----

**Scoped positionally to the render layer**, per 044. And exercised against
constructed lines rather than only against live panels, because **nothing
renders a link yet** — `S012` builds the rail. A guard that has only ever run
over zero linked tokens has not been shown to fire, which is `OBS-037`'s shape
and this project's most repeated defect.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from live.tui.links import (LINK_HUE, check_links, link, linked_tokens,
                            orphan_links)
from live.tui.links import _CLOSE as C, _OPEN as O

#: §4.1a's own example, verbatim in shape: a rail row naming four levels, and a
#: note for each. **The notes are in the same order as the entries** — nothing
#: depends on it, the repeated token already pairs them, but it removes a scan.
PAIRED_PANEL = [
    "  above  PMH ⟦PML⟧ · ORL5 · LOD · ⟦PDL⟧ PDO ⟦PDC⟧ ⟦PDH⟧ · PWL PWO",
    "         > clear for 1.4ADR",
    "         ⟦PML⟧ $722.80 gapped over",
    "         ⟦PDL⟧ $722.92 reclaimed 11:04:12h ET",
    "         ⟦PDC⟧ $726.80 gapped over",
    "         ⟦PDH⟧ $727.25 lost 13:38:40h ET",
]


def test_the_hue_is_violet_and_is_not_one_of_the_four_kinds() -> None:
    """**Christoph's ruling, and the constraint that makes it safe.**

    §4.1 binds blue, amber, green and red to kinds. The link hue must not be any
    of them: reusing one would make a link readable as the kind it borrowed,
    which is precisely the verdict §4.1 exists to prevent.
    """
    assert LINK_HUE == "violet"
    assert LINK_HUE not in {"blue", "amber", "green", "red", "white", "grey"}


def test_a_fully_paired_panel_passes() -> None:
    assert orphan_links(PAIRED_PANEL) == {}
    check_links(PAIRED_PANEL)          # must not raise


def test_an_orphaned_link_is_found_and_named() -> None:
    """**044's red: a linked token emitted with no matching note.**"""
    # Drop the ⟦PDH⟧ note and keep the token in the rail row.
    broken = [ln for ln in PAIRED_PANEL if not ln.strip().startswith("⟦PDH⟧")]

    assert orphan_links(broken) == {"PDH": 1}

    with pytest.raises(ValueError) as excinfo:
        check_links(broken)
    message = str(excinfo.value)
    assert "PDH" in message, message
    assert "never appears alone" in message, message


def test_the_refusal_is_loud_rather_than_a_fallback() -> None:
    """**044's exit test.** *A linked token emitted with no matching note ⇒ the
    render fails loudly rather than shipping a colour that means nothing.*

    A quiet fallback — dropping the colour, or rendering it anyway — would put
    verdict colour back on screen through the one channel that was added on the
    promise that it could not carry one.
    """
    with pytest.raises(ValueError):
        check_links(["  ⟦VWAP⟧ $730.68 bar-derived"])


def test_a_note_with_no_value_is_equally_an_orphan() -> None:
    """**Both directions.** A note whose token never appears above it is a
    legend for something that is not on screen, and reads as a missing row."""
    assert orphan_links(["         ⟦PML⟧ $722.80 gapped over"]) == {"PML": 1}


def test_link_refuses_to_mark_an_empty_or_already_marked_token() -> None:
    assert link("PDL") == O + "PDL" + C
    with pytest.raises(ValueError):
        link("")
    with pytest.raises(ValueError):
        link("   ")
    with pytest.raises(ValueError):
        link(O + "PDL" + C)


def test_tokens_are_found_across_the_whole_panel_not_only_the_rail() -> None:
    """§4.1a applies to **every panel**, not only the level rail — a basis note,
    a caveat, a refusal reason, a window definition."""
    lines = [
        "TRADE      ⟦LCC5⟧ the current candle is still forming",
        "ATTACHED   ⟦VWAP⟧ bar-derived, anchored 04:00h ET",
        "  stop      $48.12 ⟦LCC5⟧",
        "  VWAP      $730.68 ⟦VWAP⟧",
    ]
    assert set(linked_tokens(lines[0])) == {"LCC5"}
    assert orphan_links(lines) == {}
    check_links(lines)


def test_a_kind_colour_is_not_replaced_by_the_link() -> None:
    """**Constraint 3, asserted on the shape of the line.**

    §4.1a: *`unavailable (splice unverified)` stays amber. Only `⟦VWAP⟧` is
    linked.* The link marks the token that names WHICH row the explanation
    belongs to — never the refusal text itself, which keeps its own kind.
    """
    row = "  VWAP      ⟦VWAP⟧ — (unavailable: splice unverified)"
    note = "  ⟦VWAP⟧ tick-derived is unavailable, splice unverified"
    assert linked_tokens(row) == ["VWAP"]
    assert "unavailable" not in linked_tokens(row)
    check_links([row, note])


def test_the_live_panels_emit_no_orphaned_links_today() -> None:
    """The real render, checked. **Currently zero linked tokens** — `S012` builds
    the rail — and this is stated rather than left to look like coverage.

    It is kept because it is the assertion that starts mattering the day a panel
    first emits one, and because the constructed cases above already prove the
    guard fires.
    """
    from live.tui.app import render_panels
    from live.tui.day_record import empty_record
    from live.tui.layout import Layout

    panels = render_panels(empty_record(), Layout.load())
    lines = [row for panel in panels.values() for row in panel.rows]

    assert orphan_links(lines) == {}
    total = sum(len(linked_tokens(ln)) for ln in lines)
    assert total == 0, (
        f"a panel now emits {total} linked tokens. That is not a failure — it "
        f"means S012 has started, and this test is now doing real work rather "
        f"than standing by.")

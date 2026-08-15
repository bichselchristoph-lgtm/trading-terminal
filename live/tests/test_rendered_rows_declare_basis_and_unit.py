"""038 Part 5 tests 3 and 4 — no rendered number is bare.

**Scoped positionally to the render layer**, as 038 requires. A repo-wide search
for bare numbers matches its own fixtures — the self-reference trap 038 names as
having caught five people in one session — so these assert against the strings
`context_rows()` actually produces for a fully-populated attachment.

Two properties, and they fail for different reasons:

* **Every numeric row names a session basis or a clock anchor.** Without it, ADR
  and ATR sit four rows apart, are both labelled volatility, are computed on
  different sessions deliberately, and a reader compares them. It took a UAT and
  four chart screenshots to settle what one field in the detail column answers
  permanently.
* **Every numeric row carries a unit.** `13.14`, `1.63`, `0.86` and `47.00` are
  four kinds of quantity rendered identically, with the reader supplying the
  kinds from memory.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.indicators.context import Measured, Unit
from live.attach.attach import attach
from live.tui.app import CONTEXT_ORDER, RAIL_ORDER, measured_cell
from live.tui.numbers import FORMATS, NO_BASIS, format_value, needs_basis

from .test_attach import Fake

#: The windows and anchors a row may legitimately name. **A closed vocabulary** —
#: if a row invents a seventh, that is a ruling somebody has to make, not a string
#: a renderer may produce.
DECLARED_BASES = ("09:30-16:00 ET", "04:00-20:00 ET", "04:00-09:30 ET",
                  "09:30-09:35 ET", "09:30-09:45 ET", "04:00 anchor")

#: What a rendered unit looks like. Mirrors `config/formatting.yaml`.
#: **042 Part 2: `ADR` lost its leading space.** `0.19ADR`, not `0.19 ADR`.
UNIT_MARKS = ("$", "%", "ADR", "×", " sh", " levels")

#: **042 Part 2, the spacing rule, as data.** `(unit, marker, space_before)`.
#: The unit is attached with NO space -- `0.19ADR`, `$733.14`, `36%`, `6.1×` --
#: and **share counts are the one exception**, because `280ksh` is unreadable.
#:
#: `count`'s ` levels` keeps its space for the same reason `sh` does: it is a
#: NOUN, not a unit symbol, and 042's exception is about readability rather
#: than about the specific string `sh`. Stated here because the rule as written
#: names only `sh`, and a reader applying it literally would close up ` levels`.
SPACING = (
    (Unit.DOLLAR,   "$",       False),
    (Unit.PERCENT,  "%",       False),
    (Unit.ADR,      "ADR",     False),
    (Unit.MULTIPLE, "×",       False),
    (Unit.SHARES,   "sh",      True),
    (Unit.COUNT,    "levels",  True),
)


def numeric_rows() -> list[tuple[str, Measured, str]]:
    """`(row name, the Measured, the rendered line)` for every row with a NUMBER.

    Refusals are excluded deliberately: an absent `Measured` already names its
    own reason and has nothing to declare a basis for.

    **The `Measured` is carried alongside the string rather than the string
    being sniffed**, so the basis exemption below can be taken from the renderer's
    own `needs_basis` instead of from a substring. Two copies of that rule would
    drift, and the copy in the test is the one that would quietly widen.
    """
    result = attach("QQQ", Fake())
    assert result.attached and result.context, "the fixture attach did not fill"
    out = []
    for name in (*CONTEXT_ORDER, *RAIL_ORDER):
        m = result.context.get(name) or result.rail.get(name)
        if m is None or not m.ok:
            continue
        out.append((name, m, f"{name:<9} {measured_cell(m)}"))
    return out


def test_the_fixture_actually_renders_rows() -> None:
    """**Guards the two tests below from passing on an empty list.**

    A test that iterates nothing is green, and this file's whole job is to
    iterate over rendered rows — so the count is asserted before the properties
    are. `OBS-037`'s shape: a check that passes trivially.
    """
    rows = numeric_rows()
    assert len(rows) >= 15, (
        f"only {len(rows)} numeric rows rendered; the context block and rail "
        f"together carry far more. The properties below would pass vacuously.")


def test_every_rendered_number_names_its_basis_or_anchor() -> None:
    """**Test 3.**"""
    # **The exemption comes from `needs_basis`, the renderer's own function** —
    # a pure count is arithmetic on a price, not a measurement over bars.
    missing = [line for _, m, line in numeric_rows()
               if needs_basis(m) and not any(b in line for b in DECLARED_BASES)]
    assert not missing, (
        "these rows render a number and do not say which session it was "
        "computed over:\n" + "\n".join(f"  {m}" for m in missing)
        + f"\n**A value that carries its basis can be compared with something; "
          f"a value that does not can only be argued about.** Declared "
          f"windows: {', '.join(DECLARED_BASES)}.")


def test_every_rendered_number_carries_a_unit() -> None:
    """**Test 4.** 038 Part 2 — all numbers need units, always.

    **Asserted against the rendered VALUE, not the whole line**, and that
    distinction was found by mutation rather than by reading. Checking the line
    let the row *name* satisfy the check: `ADR%` begins with the label `ADR%`, so
    stripping the `%` off the percent unit still left a `%` in the string and the
    test stayed green while the number went bare. **A test that matches the label
    it prints beside the value is checking its own output** — the self-reference
    trap 038 names, and it survived one round here.
    """
    missing = [f"{name}: {format_value(m)}" for name, m, _line in numeric_rows()
               if not any(u in format_value(m) for u in UNIT_MARKS)]
    assert not missing, (
        "these rows render a bare number with no unit:\n"
        + "\n".join(f"  {m}" for m in missing)
        + f"\n**All numbers need units** (038 Part 2). Expected one of: "
          f"{', '.join(repr(u) for u in UNIT_MARKS)}.")


def test_a_value_with_no_basis_refuses_rather_than_rendering_bare() -> None:
    """**038's exit test, and it is the refusal half of test 3.**

    A row whose basis is missing must render `unavailable (no basis declared)`,
    **never an unlabelled number.** Failing open here would mean the first
    indicator somebody adds without a basis renders a plausible figure — which is
    the exact failure mode of the value this task was written to fix.
    """
    no_basis = Measured(value=15.61, sample="Wilder RMA, n=14",
                        unit=Unit.DOLLAR, basis=None)
    rendered = measured_cell(no_basis)
    assert NO_BASIS in rendered, (
        f"a Measured with no basis rendered {rendered!r}. It must refuse by "
        f"name instead.")
    assert "15.61" not in rendered, (
        f"the number survived a missing basis: {rendered!r}. An unlabelled "
        f"number on this panel is the whole defect.")


def test_a_pure_count_is_exempt_and_renders() -> None:
    """**The exemption, asserted so it cannot quietly widen.**

    `round` counts half-dollar levels within a span of a price. It is arithmetic
    on a price, not a measurement over bars, so it has no session to name and
    demanding one would produce a label that was not true. **Every other unit is
    a measurement over bars.**
    """
    count = Measured(value=47.0, sample="half-dollar levels within ±$11.83 "
                                        "of $733.14", unit=Unit.COUNT, basis=None)
    rendered = measured_cell(count)
    assert NO_BASIS not in rendered, "a count must not be forced to name a session"
    assert "47 levels" in rendered, (
        f"a count rendered as {rendered!r}. 038 Part 6 row 2: `round 47.00` beside "
        f"PDH and ORL on a 733 instrument reads as a price, and nothing near 47 "
        f"is a round level for anything near 733.")


@pytest.mark.parametrize("unit,value,expected", [
    (Unit.DOLLAR, 733.14, "$733.14"),
    (Unit.DOLLAR, 0.9412, "$0.9412"),      # §4.0a — 4 decimals below $1.00
    (Unit.PERCENT, 1.6349, "1.6%"),        # §4.0a — one decimal
    (Unit.ADR, 1.44, "1.4ADR"),          # 042 Part 2 — no space
    (Unit.MULTIPLE, 6.14, "6.1×"),
    (Unit.SHARES, 18_119_366, "18.1M sh"),  # §4.0a — abbreviated above 1M
    (Unit.SHARES, 265, "265 sh"),
    (Unit.COUNT, 47, "47 levels"),
])
def test_the_formatter_matches_spec_4_0a(unit: Unit, value: float,
                                         expected: str) -> None:
    """**038 Part 6 row 3.** `ADR used` and `round` rendered two decimals where
    §4.0a requires one for a ratio and none for a count.

    The cause was one hardcoded `f"{m.value:,.2f}"` in `live/tui/app.py` serving
    every quantity on the panel — which also produced `18,119,366.00` for a share
    count, decimals and all, where §4.0a asks for `18.1M sh`.
    """
    assert FORMATS[unit].render(value) == expected

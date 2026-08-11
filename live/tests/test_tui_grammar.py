"""The refusal grammar, and the re-authored `Result` model.

**This is the behavioural test S009 §3 requires** — it shows that `state=None`
with an `na_reason` renders differently from `state=False`, and that `degraded`
survives a round trip. Not an import smoke test: every assertion is on a
rendered result.

`live/render.py` was NOT adopted (see `grammar.Result`'s docstring), so this
covers the re-authored model rather than an adopted one.
"""
from __future__ import annotations

import pytest

from live.tui.grammar import (ABSENT_NOT_ZERO, EMPTY, NOT_BUILT, Cell, Confidence,
                              Freshness, Presence, Result)


def test_state_none_with_reason_is_not_state_false() -> None:
    """**The distinction the whole grammar exists for.**

    `state=None` is a refusal — the thing could not be measured. `state=False`
    is a real negative verdict. Rendering them alike is how a panel shows a
    value with nothing behind it.
    """
    refused = Cell.from_result(Result(state=None, na_reason="no source wired"))
    verdict = Cell.from_result(Result(state=False, quantifier="no"))

    assert refused.render() != verdict.render()
    assert refused.presence is Presence.ABSENT
    assert verdict.presence is Presence.PRESENT
    assert "no source wired" in refused.render()
    assert refused.render().startswith(EMPTY)


def test_degraded_survives_the_round_trip() -> None:
    r = Result(state=True, quantifier="1.4 ADR", degraded=True,
               degraded_reason="odd-lot filtered feed")
    c = Cell.from_result(r)
    assert c.confidence is Confidence.DEGRADED
    out = c.render()
    assert "1.4 ADR" in out
    assert "odd-lot filtered feed" in out
    assert out != "1.4 ADR", "a degraded value must not render as a plain number"


def test_a_plain_number_renders_plain() -> None:
    """The one path to a bare number: all three axes nominal."""
    c = Cell.from_result(Result(state=True, quantifier="1.4 ADR"))
    assert c.is_plain
    assert c.render() == "1.4 ADR"


@pytest.mark.parametrize("cell", [
    Cell.absent("no account snapshot"),
    Cell.not_yet(),
    Cell.no_source(),
    Cell.from_result(Result(state=None, na_reason="unavailable")),
])
def test_absence_never_renders_as_zero(cell: Cell) -> None:
    """**Tenet 2, at the only layer that can enforce it.**

    Presence renders `—`, never `0.00`. Zero is a finding; absence is not.
    """
    out = cell.render()
    assert "0.00" not in out
    assert "0" != out.strip()
    assert EMPTY in out
    assert cell.reason, "an absent cell must carry a reason"


def test_every_non_nominal_cell_renders_its_reason() -> None:
    """*Any deviation renders differently AND renders the reason.*"""
    for cell in (Cell.absent("r1"), Cell.degraded("1.2", "r2"),
                 Cell.unfitted(), Cell.stale("1.2", "42s"),
                 Cell.frozen("1.2", "08:00"), Cell.not_yet("r3")):
        assert not cell.is_plain
        assert cell.reason
        assert cell.reason in cell.render(), f"{cell} dropped its reason"


def test_not_built_is_a_named_badge_not_a_blank() -> None:
    out = Cell.not_built().render()
    assert NOT_BUILT in out
    assert out.strip() != ""


def test_freshness_presence_confidence_are_orthogonal() -> None:
    """`SPEC.md` §4: three axes, each with its own channel, never collapsed."""
    c = Cell(text="1.2", freshness=Freshness.STALE, presence=Presence.PRESENT,
             confidence=Confidence.DEGRADED, reason="both")
    assert c.freshness is Freshness.STALE
    assert c.confidence is Confidence.DEGRADED
    assert not c.is_plain


def test_absent_defaults_to_the_canonical_vocabulary() -> None:
    """A refusal with no reason supplied still names one from `SPEC.md` §4."""
    assert ABSENT_NOT_ZERO in Cell.absent("").render()

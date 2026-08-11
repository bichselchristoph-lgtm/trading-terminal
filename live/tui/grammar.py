"""The refusal grammar — the only place a value becomes a string.

`SPEC.md` §4 defines three orthogonal axes, each with its own channel, never
collapsed into one grey. This module is that spec as typed values.

**A cell that is fresh, present and full-confidence renders as a plain number.
Any deviation renders differently AND renders the reason.** That is the whole
contract, and it is enforced here rather than in each panel, because a rule
applied in nine places is a rule that will be applied in eight.

**Presence renders `—`, never `0.00`.** Tenet 2, at the only layer that can
enforce it. A panel that renders a value with nothing behind it is worse than a
panel that renders nothing — Layer 0 rendered as an operational reading when
none of its fourteen rows existed, and no test failed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

#: `SPEC.md` §4's canonical vocabulary, verbatim. Anything rendered as a refusal
#: uses one of these strings; a new one is a spec change, not a code change.
UNFITTED = "unfitted"
UNTESTED = "untested"
PARTIAL = "partial"
ABSENT_NOT_ZERO = "absent, not zero"
SUPERSEDED = "superseded"
FLAGGED_NOT_ERROR = "flagged, not an error"
REDUCED_DENOMINATOR = "reduced denominator"
NOT_BUILT = "NOT BUILT"
STALE = "STALE"
FROZEN = "FROZEN"
WARMING = "warming"
NO_SOURCE = "no-source"

#: The em-dash placeholder. NOT "0.00", NOT "" — an absent value must be
#: visually distinct from a measured zero, because zero is a finding.
EMPTY = "—"


class Freshness(Enum):
    LIVE = "live"
    AGED = "aged"
    STALE = "stale"
    FROZEN = "frozen"          # renders as frozen-at-HH:MM via `frozen_at`


class Presence(Enum):
    PRESENT = "present"
    ABSENT = "absent"
    NOT_YET_COMPUTED = "not-yet-computed"


class Confidence(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    REFUSED = "refused"
    UNFITTED = "unfitted"


@dataclass
class Result:
    """Re-authored from `live/detectors.py`, NOT adopted.

    `BUILD-PLAN.md` step 3 says to port `live/render.py`'s `Result` model
    unchanged. Two things were found on contact:

    1. **`Result` is not in `render.py`.** It is defined in `live/detectors.py`
       and imported. The plan names the wrong module.
    2. **Adopting `render.py` drags a four-module closure** — itself plus
       `detectors.py`, `marketstate.py` and `feeds.py`, the last of which still
       imports the unmaintained `ib_insync`. S009 §3 says to stop on a cascade
       and re-author rather than adopt a second module to satisfy the first.

    So the four meaningful fields are reproduced here with their semantics
    intact, and `live/render.py` remains un-adopted. The `quantifier`, `detail`
    and `value` fields come across too, because dropping them would be a
    redesign and the instruction was explicitly not to redesign it.
    """

    state: Optional[bool]
    quantifier: str = ""
    detail: str = ""
    value: Optional[float] = None
    na_reason: str = ""
    #: True when the verdict is real but the feed cannot support it at full
    #: fidelity. Rendered with a marker so it is never read as an
    #: equal-confidence result.
    degraded: bool = False
    degraded_reason: str = ""


@dataclass
class Cell:
    """One rendered value, with its three axes and its reason.

    Construct through the classmethods rather than directly — each one names the
    refusal it represents, so a reader of the call site sees *why* a cell is not
    a number.
    """

    text: str
    freshness: Freshness = Freshness.LIVE
    presence: Presence = Presence.PRESENT
    confidence: Confidence = Confidence.FULL
    reason: str = ""
    frozen_at: str = ""

    # ---- constructors, one per refusal shape -------------------------------

    @classmethod
    def value(cls, text: str, *, freshness: Freshness = Freshness.LIVE) -> "Cell":
        """A real measurement. The ONLY path to a plain number."""
        return cls(text=text, freshness=freshness)

    @classmethod
    def absent(cls, reason: str) -> "Cell":
        return cls(text=EMPTY, presence=Presence.ABSENT,
                   confidence=Confidence.REFUSED, reason=reason or ABSENT_NOT_ZERO)

    @classmethod
    def not_yet(cls, reason: str = WARMING) -> "Cell":
        return cls(text=EMPTY, presence=Presence.NOT_YET_COMPUTED,
                   confidence=Confidence.REFUSED, reason=reason)

    @classmethod
    def not_built(cls, reason: str = "no file for today") -> "Cell":
        return cls(text=f"[ {NOT_BUILT} ]", presence=Presence.ABSENT,
                   confidence=Confidence.REFUSED, reason=reason)

    @classmethod
    def no_source(cls, reason: str = NO_SOURCE) -> "Cell":
        return cls(text=EMPTY, presence=Presence.ABSENT,
                   confidence=Confidence.REFUSED, reason=reason)

    @classmethod
    def degraded(cls, text: str, reason: str) -> "Cell":
        return cls(text=text, confidence=Confidence.DEGRADED, reason=reason)

    @classmethod
    def unfitted(cls, text: str = EMPTY) -> "Cell":
        return cls(text=text, confidence=Confidence.UNFITTED, reason=UNFITTED)

    @classmethod
    def stale(cls, text: str, age: str) -> "Cell":
        return cls(text=text, freshness=Freshness.STALE, reason=f"{STALE} {age}")

    @classmethod
    def frozen(cls, text: str, at: str) -> "Cell":
        return cls(text=text, freshness=Freshness.FROZEN, frozen_at=at,
                   reason=f"{FROZEN} at {at}")

    @classmethod
    def from_result(cls, r: Result) -> "Cell":
        """The bridge from the detector model to the grammar.

        `state=None` with an `na_reason` is a REFUSAL and must not render like
        `state=False`, which is a real negative verdict. That distinction is the
        one `test_tui_grammar` pins.
        """
        if r.state is None:
            return cls.absent(r.na_reason or ABSENT_NOT_ZERO)
        text = r.quantifier or ("yes" if r.state else "no")
        if r.degraded:
            return cls.degraded(text, r.degraded_reason or PARTIAL)
        return cls.value(text)

    # ---- rendering ---------------------------------------------------------

    @property
    def is_plain(self) -> bool:
        """True only when all three axes are nominal. The plain-number case."""
        return (self.freshness is Freshness.LIVE
                and self.presence is Presence.PRESENT
                and self.confidence is Confidence.FULL)

    def render(self) -> str:
        """A plain number when nominal; otherwise the value AND the reason.

        Never returns a bare number for a non-nominal cell, and never returns
        `0.00` for an absent one.
        """
        if self.is_plain:
            return self.text
        marker = {
            Confidence.DEGRADED: "~",
            Confidence.REFUSED: "",
            Confidence.UNFITTED: "?",
            Confidence.FULL: "",
        }[self.confidence]
        body = f"{marker}{self.text}" if marker else self.text
        return f"{body} ({self.reason})" if self.reason else body

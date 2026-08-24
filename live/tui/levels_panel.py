"""090 — the LEVELS panel: the ten that already compute, against mockup v1.5
(`LEVELS mockup — the rail against the running terminal - LATEST`).

**Confirmed from the code, not from any document — 090 Part 0.** `level_rail`
(`core/indicators/context.py`) computes twelve keys on a live attach:
`PDH PDL PMH PML ORH5 ORL5 ORH15 ORL15 52wH 52wL VWAP round` — `RAIL_ORDER`
(`app.py`) lists eleven and omits `VWAP`. Two of the twelve (`VWAP`, `round`)
are not LEVELS-SPEC levels at all; `round` is a DETECTION (a count of
half-dollar increments within +/-ADR$), not a DEFINITION, and LEVELS §6 rules
detections out. **Ten of LEVELS-SPEC's twenty-three are built.** The other
thirteen — `HOD LOD PDO PDC PWH PWO PWL PWC MoMH MoMO MoML MoMC ATH` — are not,
and render as one grouped absent row, per this task's own §4.

**`ATH` has never been computed anywhere in this tree's history** (`git log
-S ATH` shows only comments about `LONG_BASIS`'s own naming rationale) —
LEVELS §9.1's cited UAT could not have been reading this application's own
`ATH` row.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.indicators.context import Measured

#: **LEVELS-SPEC's own twenty-three**, confirmed against the code by 090's
#: own Part 0 — never against a document, per the task's own instruction
#: ("the last two attempts to state it from outside the code were both
#: wrong").
ALL_23 = (
    "HOD", "LOD", "PDO", "PDC", "PMH", "PML",
    "PWH", "PWO", "PWL", "PWC",
    "MoMH", "MoMO", "MoML", "MoMC",
    "ATH",
    "ORH5", "ORL5", "ORH15", "ORL15",
    "PDH", "PDL", "52wH", "52wL",
)
assert len(ALL_23) == 23, f"LEVELS-SPEC names {len(ALL_23)}, not 23"

#: **The thirteen not built.** `090`'s own scope stops at rendering these as
#: one grouped absent row — building any of them is the session module's
#: task (`B-043`) and the one after it, per §7 "Not in this task".
NOT_BUILT = ("HOD", "LOD", "PDO", "PDC", "PWH", "PWO", "PWL", "PWC",
             "MoMH", "MoMO", "MoML", "MoMC", "ATH")

#: **The ten `level_rail` actually computes** — confirmed live, 090 Part 0
#: item 1. Order matches the mockup's own reading order within each half,
#: not `RAIL_ORDER` (which predates this task and omits `VWAP`).
BUILT = ("PMH", "PML", "ORH5", "ORL5", "ORH15", "ORL15",
        "PDH", "PDL", "52wH", "52wL")

assert set(BUILT) | set(NOT_BUILT) == set(ALL_23)
assert not (set(BUILT) & set(NOT_BUILT))

#: Mockup v1.5 §0 / Amendment 3 — the hysteresis band. **1.10 is UNFITTED**:
#: nothing has measured how often levels sit near the boundary (the
#: mockup's own words, carried verbatim). Renders as unfitted wherever
#: provenance shows.
ENTER_ADR = 1.00
LEAVE_ADR = 1.10

#: Amendment 1 — per side, never a global sort.
MAX_PER_SIDE = 5

#: Mockup §4's own footnote — rides on `PDC`'s row, never a separate line.
GAPPED_OVER = "gapped over — no trade there today"


@dataclass
class LevelsResult:
    rows: list
    caption: str
    included: frozenset


def _fmt_price(v: float) -> str:
    return f"${v:,.2f}"


def _fmt_dist(v: float) -> str:
    """**Deliberately ASCII `-`, not the mockup's own `−` (U+2212).** This
    module cannot import `app.py`'s `ascii_safe()` without a circular
    import (`app.py` imports this module, not the reverse), and a SECOND,
    unguarded Unicode minus is exactly the failure `ascii_safe()` exists to
    prevent for every other glyph on screen — measured directly: printing
    `−` crashed a plain `cp1252` console with `UnicodeEncodeError` while
    building this module. Recorded as a deliberate, narrow deviation from
    the mockup's own glyph, not an oversight."""
    sign = "+" if v >= 0 else "-"
    return f"{sign}${abs(v):,.2f}"


def update_levels_included(rail: dict, price: Optional[float],
                           previous: frozenset) -> frozenset:
    """**Amendment 3, the memory step.** Computes the NEW currently-included
    set from `rail`/`price` and the PREVIOUSLY-included set — a level not
    currently included enters at `<= ENTER_ADR`; one already included
    leaves only past `LEAVE_ADR`. Truncated to `MAX_PER_SIDE` per side
    afterward, because the persisted set must be what is ACTUALLY
    RENDERED — a level dropped by truncation re-enters at `ENTER_ADR` next
    time, never coasting on the wider `LEAVE_ADR` band it did not actually
    leave by distance.

    **Called by `app.py`, never by `render_panels`** — `render_panels`
    stays a pure function of whatever this already wrote; this is the one
    place `Attached.levels_included` is mutated.
    """
    adr = rail.get("ADR $")
    if price is None or adr is None or not adr.ok or adr.value <= 0:
        # Amendment 4 -- filter off. Nothing is "included" by distance;
        # the caller renders everything unfiltered and does not consult
        # this set for filtering, only history resets.
        return frozenset()

    above, below = [], []
    for key in BUILT:
        m = rail.get(key)
        if m is None or not m.ok:
            continue
        dist = m.value - price
        adr_frac = abs(dist) / adr.value
        was_in = key in previous
        threshold = LEAVE_ADR if was_in else ENTER_ADR
        if adr_frac > threshold:
            continue
        (above if dist >= 0 else below).append((abs(dist), key))

    above.sort()
    below.sort()
    kept = {k for _, k in above[:MAX_PER_SIDE]} | {k for _, k in below[:MAX_PER_SIDE]}
    return frozenset(kept)


def build_levels_panel_rows(rail: dict, price: Optional[float],
                            included: frozenset) -> LevelsResult:
    """**Pure.** Builds the rendered rows and the caption from `rail`,
    `price` and the ALREADY-COMPUTED `included` set (see
    `update_levels_included`) — this function never decides membership,
    only how to DISPLAY it, so it can be called from `render_panels`
    without breaking that function's own purity.
    """
    labels = {
        "PMH": "PMH", "PML": "PML", "ORH5": "ORH5", "ORL5": "ORL5",
        "ORH15": "ORH15", "ORL15": "ORL15", "PDH": "PDH", "PDL": "PDL",
        "52wH": "52wH", "52wL": "52wL",
    }

    if price is None:
        return LevelsResult(rows=[], caption="not attached", included=frozenset())

    adr = rail.get("ADR $")
    filter_on = adr is not None and adr.ok and adr.value > 0

    computed: dict[str, Measured] = {}
    # **Grouped by reason, mockup §6's own shape** — a level that failed to
    # compute names why, and two failures sharing a reason share one row.
    absent_by_reason: dict[str, list] = {}
    for key in BUILT:
        m = rail.get(key)
        if m is None:
            # Not yet landed -- pending is its own reason, never conflated
            # with a real refusal or with "not built".
            absent_by_reason.setdefault("pending", []).append(key)
        elif not m.ok:
            reason = m.unavailable or "unavailable"
            absent_by_reason.setdefault(reason, []).append(key)
        else:
            computed[key] = m

    denominator = len(computed)

    if filter_on:
        above, below = [], []
        for key, m in computed.items():
            dist = m.value - price
            (above if dist >= 0 else below).append((dist, key, m))
        # A level in `computed` but not in `included` is outside the
        # window (or truncated) -- excluded, not absent.
        rendered_above = sorted(
            ((d, k, m) for d, k, m in above if k in included), reverse=True)
        rendered_below = sorted(
            ((d, k, m) for d, k, m in below if k in included), reverse=True)
        excluded = denominator - len(rendered_above) - len(rendered_below)
        numerator = len(rendered_above) + len(rendered_below)
        caption = f"{numerator} of {denominator} · {excluded} outside 1 ADR"
    else:
        above, below = [], []
        for key, m in computed.items():
            dist = m.value - price
            (above if dist >= 0 else below).append((dist, key, m))
        rendered_above = sorted(above, reverse=True)
        rendered_below = sorted(below, reverse=True)
        numerator = denominator
        reason = adr.unavailable if (adr is not None and not adr.ok) else "ADR unavailable"
        caption = f"{numerator} of {denominator} · filter off — {reason}"

    rows: list = []
    for dist, key, m in rendered_above:
        label = labels[key]
        line = f" {label} {_fmt_price(m.value)} {_fmt_dist(dist)}"
        if key == "PDC":
            line += f"  {GAPPED_OVER}"
        rows.append(line)

    rows.append(f" {'-'*30} price {_fmt_price(price)} {'-'*30}")

    for dist, key, m in rendered_below:
        label = labels[key]
        line = f" {label} {_fmt_price(m.value)} {_fmt_dist(dist)}"
        if key == "PDC":
            line += f"  {GAPPED_OVER}"
        rows.append(line)

    # **The not-built row — always present, never windowed.** A level with
    # no price has no distance, so a window cannot apply to it, and a
    # failure must not be able to hide by being far away.
    rows.append(" absent " + " · ".join(NOT_BUILT) + " — not built")

    for reason, keys in sorted(absent_by_reason.items()):
        rows.append(" absent " + " ".join(keys) + f" — {reason}")

    return LevelsResult(rows=rows, caption=caption, included=included)

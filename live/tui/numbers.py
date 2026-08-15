"""The one number formatter — `SPEC.md` §4.0a, units per 038 Part 2.

**One function, and its precision comes from `config/formatting.yaml`.** §4.0a's
reason is that *"two panels printing `1.4 ADR` and `1.44 ADR` for one number is a
small thing that reads as two numbers"*. Before 038 there was no such function:
`live/tui/app.py` formatted every context value as `f"{m.value:,.2f}"`, which is
why `ADR used` rendered `67.00` and `round` rendered `47.00`.

----

**Units are not decoration and this module is where 038 Part 2 lands.**
Christoph's ruling: *all numbers need units, always.* A panel column of bare
floats — `13.14`, `1.63`, `0.86`, `47.00` — is four different kinds of quantity
rendered identically, and the reader supplies the kinds from memory.

**The producer declares the unit; this module only renders it.** `Measured.unit`
is set where the number is computed, because whether `13.14` is dollars or a
multiple is a fact about the indicator. A renderer that guessed from the row's
NAME would be re-deriving something the computation already knew, and would guess
wrong on exactly the rows nobody thought about.

**Rounding is display-only and never re-enters a calculation** (§4.0a). Nothing
here is written back anywhere; `Measured.value` keeps its full precision.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from core.indicators.context import Measured, Unit

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config" / "formatting.yaml"


@dataclass(frozen=True)
class UnitFormat:
    """How one `Unit` renders. Loaded from config, never defaulted in code."""

    decimals: int
    prefix: str = ""
    suffix: str = ""
    #: §4.0a — prices carry 4 decimals below $1.00, where 2 cannot show a tick.
    decimals_below_one: Optional[int] = None
    #: §4.0a — share counts abbreviate above 1M: `18.1M sh`.
    abbreviate_above: Optional[float] = None
    abbreviated_decimals: int = 1

    def render(self, value: float) -> str:
        if self.abbreviate_above is not None and abs(value) >= self.abbreviate_above:
            scaled, suffix_mag = _abbreviate(value)
            body = f"{scaled:,.{self.abbreviated_decimals}f}{suffix_mag}"
        else:
            dp = self.decimals
            if self.decimals_below_one is not None and 0 < abs(value) < 1:
                dp = self.decimals_below_one
            body = f"{value:,.{dp}f}"
        return f"{self.prefix}{body}{self.suffix}"


def _abbreviate(value: float) -> tuple[float, str]:
    """`18,119,366` -> `(18.119366, 'M')`. **Only M and B.**

    Deliberately no `k`: §4.0a abbreviates *above 1M* and nothing below, and a
    `k` would put three magnitudes on one column where the eye is comparing
    share counts across rows.
    """
    for cut, mag in ((1_000_000_000, "B"), (1_000_000, "M")):
        if abs(value) >= cut:
            return value / cut, mag
    return value, ""


def load_formats(path: Optional[Path] = None) -> dict[Unit, UnitFormat]:
    """`config/formatting.yaml`, loaded. **Every `Unit` must be present.**

    A missing unit is a `ValueError` rather than a silent fallback to two
    decimals — that fallback is exactly what 038 Part 6 row 3 is a report of, and
    a formatter that quietly covers for its own config would reintroduce it the
    first time somebody added a `Unit` and forgot the entry.
    """
    p = path or CONFIG_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"{p} does not exist. §4.0a puts number precision in config; there "
            "is no built-in precision to fall back to, deliberately.")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    units = data.get("units")
    if not isinstance(units, dict):
        raise ValueError(f"{p}: no `units:` mapping.")

    out: dict[Unit, UnitFormat] = {}
    for unit in Unit:
        entry = units.get(unit.value)
        if not isinstance(entry, dict):
            raise ValueError(
                f"{p}: no entry for unit `{unit.value}`. Every Unit renders "
                "through this file; an absent one has no precision at all.")
        if "decimals" not in entry:
            raise ValueError(f"{p}: `{unit.value}` has no `decimals`.")
        if not str(entry.get("note") or "").strip():
            # Same rule `config/ibkr.yaml` holds its settings to: the reason a
            # setting has the value it has is exactly what nobody can
            # reconstruct later.
            raise ValueError(
                f"{p}: `{unit.value}` has no `note`. Every setting says why it "
                "is what it is.")
        out[unit] = UnitFormat(
            decimals=int(entry["decimals"]),
            prefix=str(entry.get("prefix") or ""),
            suffix=str(entry.get("suffix") or ""),
            decimals_below_one=(int(entry["decimals_below_one"])
                                if entry.get("decimals_below_one") is not None
                                else None),
            abbreviate_above=(float(entry["abbreviate_above"])
                              if entry.get("abbreviate_above") is not None
                              else None),
            abbreviated_decimals=int(entry.get("abbreviated_decimals", 1)))
    return out


#: Loaded once. The file is read at import, so a malformed config fails the
#: program rather than one row of one panel at 09:31.
FORMATS = load_formats()


#: **The refusal a row renders when it arrives with no basis.** 038's exit test:
#: *a row whose basis constant is missing renders `unavailable (no basis
#: declared)`, never an unlabelled number.*
NO_BASIS = "no basis declared"


def format_value(m: Measured) -> str:
    """The number, with its unit. **Value only — the caller adds the sample.**"""
    return FORMATS[m.unit].render(m.value)


def basis_label(m: Measured) -> Optional[str]:
    """The session window this value was computed on, as it renders.

    `None` where the quantity genuinely has no session — a pure count of round
    numbers is arithmetic on a price, not a measurement over bars. Everything
    else that arrives without one is refused by `measured_cell`.
    """
    return m.basis.label if m.basis is not None else None


def needs_basis(m: Measured) -> bool:
    """**Which values must declare a session, and it is not all of them.**

    A `COUNT` is derived from a price and a span, not from a bar series, so it
    has no session to name and demanding one would produce a label that was not
    true. Every other unit is a measurement over bars.
    """
    return m.unit is not Unit.COUNT

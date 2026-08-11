"""The thin day record — S009 §4c.

**`regime_snapshot` is a pointer, not rows.** There is no `layer_0`, no
`layer_1`, no `layer_i` and no `exposure` field, and none may be added "for
later".

**A field that does not exist cannot be rendered by accident.** That is
`SPEC.md` §4.1 enforced one layer below the screen: the Layer 0 composite
rendered as an operational reading because the field was there to render. The
cheapest place to stop that is the record definition.

`renderer(record)` is a **pure function of this object**. No panel reaches around
it to compute anything — everything downstream leans on that, and retrofitting
it later costs ten times as much.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

SCHEMA_VERSION = 1


@dataclass
class RegimeSnapshotRef:
    """A POINTER. `SPEC.md` §3.2: the terminal renders nothing from the snapshot.

    `ref` may be absent, which is a state and not an error — it renders as
    `[ NOT BUILT ]`, and per §5.1a as `[ NOT BUILT — OVERDUE Nh ]` once the
    scheduled time has passed.
    """

    ref: Optional[str] = None
    frozen_at: Optional[str] = None


@dataclass
class Ticket:
    symbol: str
    state: str
    detail: str = ""


@dataclass
class Attached:
    symbol: str
    since: str = ""


@dataclass
class Health:
    """S009 §4g. Source states, last-seen ages, and the ticks-received versus
    frames-painted ratio — permanently visible, never hidden."""

    sources: dict[str, str] = field(default_factory=dict)
    last_seen: dict[str, str] = field(default_factory=dict)
    ticks_received: int = 0
    frames_painted: int = 0


@dataclass
class DayRecord:
    """Deliberately thin. Adding a field here is a spec decision, not a
    convenience — see the module docstring."""

    schema_version: int = SCHEMA_VERSION
    session_date: Optional[str] = None
    generated_at: Optional[str] = None
    attached: list[Attached] = field(default_factory=list)
    tickets: list[Ticket] = field(default_factory=list)
    health: Health = field(default_factory=Health)
    regime_snapshot: RegimeSnapshotRef = field(default_factory=RegimeSnapshotRef)
    #: One number per session, for the monthly P&L accumulator. Not a panel.
    session_pnl: Optional[float] = None


def empty_record() -> DayRecord:
    """The record the app boots on, and the one the canonical snapshot uses.

    Everything absent. Every surface must render a NAMED REFUSAL against this —
    no crashes, no blanks, no zeros. That assertion is this slice's whole point.
    """
    return DayRecord()

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
    """One attached symbol, **and the context block that was measured for it.**

    **Why fields were added to a record whose docstring says not to (034).**
    `attach()` has computed `context` and `rail` since S010 and `Attached` had
    nowhere to put them, so every value the slice exists to produce was
    discarded one line after it was measured. That is the fifth instance in this
    tree of *computed and unreachable* — after the app with no entry point, the
    palette that lived in a docstring, `attach()` with no key, and
    `IBKRMarketData` imported by nothing.

    **These are `Measured`s, not strings.** `render_panels` is a pure function of
    this record and formatting is its job; storing pre-rendered rows here would
    put the refusal grammar in two places, and `grammar.py` exists so that it is
    in one.

    The docstring's prohibition is about fields that make an UNBUILT reading
    representable — `layer_0`, `exposure`. These hold values that already exist
    on `AttachResult`, measured by code that shipped under S010.
    """

    symbol: str
    since: str = ""
    #: `AttachResult.context` — ADR, ATR, extension, VWAP, cum vol, both RVOLs.
    context: dict = field(default_factory=dict)
    #: `AttachResult.rail` — PDH/PDL, PMH/PML, ORH/ORL, VWAP, 52-week, rounds.
    rail: dict = field(default_factory=dict)
    #: Where the numbers came from and how old they are. **Block-level, and that
    #: is a stated limitation rather than a shortcut**: `Measured` carries a
    #: `sample` but has no as-of or lag field, so a per-value stamp is not
    #: something this task can render. See the done-note.
    source: str = ""
    as_of: str = ""
    lag: str = ""
    #: What step 4 said. An attach with no tape is still an attach (S010).
    tape: str = ""
    slot_state: str = ""
    #: **058 Part 3.** `AttachResult.partial` — "N of M rows unavailable"
    #: when the gather completed with some requests refusing. Empty when
    #: everything measured. Tenet 3, rendered rather than merely true.
    partial: str = ""


@dataclass
class Health:
    """S009 §4g. Source states, last-seen ages, and the ticks-received versus
    frames-painted ratio — permanently visible, never hidden."""

    sources: dict[str, str] = field(default_factory=dict)
    #: name -> **why it is not there** (034 part 3). A source that connected is
    #: in `sources`; one that refused is here, carrying host, port and reason.
    #:
    #: **Two dicts rather than one with a magic state string.** The renderer has
    #: to choose between a value and a refusal cell, and inferring that by
    #: matching words in a state string would put the grammar's decision inside
    #: a substring test. Empty-and-empty is still the third case — *nothing ever
    #: tried to connect* — which is what an empty record renders and is not the
    #: same fact as a refusal.
    unavailable_sources: dict[str, str] = field(default_factory=dict)
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
    #: **Why a field was added to a record whose docstring says not to (032).**
    #:
    #: `SPEC.md` §4.2 requires a failed attach to be *surfaced, not refused* — the
    #: reason renders in the ATTACHED panel and the app stays up. But
    #: `render_panels(record)` is a PURE function of this object, so a refusal the
    #: renderer cannot see is a refusal that cannot render. The alternative was to
    #: hand `render_panels` a second argument, which breaks the one property
    #: everything downstream leans on.
    #:
    #: **It is a rendered reason, not a layer.** The docstring's prohibition is
    #: about fields that make an unbuilt reading *representable* — `layer_0`,
    #: `exposure` — and this holds a string that already exists on
    #: `AttachResult.refusal`. It is cleared on the next successful attach, so it
    #: describes the last attempt and never accumulates.
    attach_refusal: str = ""
    #: **058 Part 3 — the one screen-level state an attach's gather is in
    #: flight under.** The symbol being attached, or `""` when nothing is.
    #: Not a layer either: it is a rendered reason for why the panel shows
    #: nothing new yet, cleared the instant the gather lands (success or
    #: refusal) so it never survives past the attach it names.
    attaching: str = ""
    #: **070 §6 — a re-attach refused inside the same-contract cooldown.**
    #: `"<symbol> <remaining>"` (e.g. `"QQQ 11s"`), never split into two
    #: fields: `attach_refusal` already carries a colon-joined symbol+reason
    #: for the same reason, and one field is enough for a state this
    #: short-lived. Cleared the instant the next attach begins or lands, so
    #: it never survives past the attempt it names — same lifecycle as
    #: `attaching` and `attach_refusal`, which it is mutually exclusive with.
    attach_queued: str = ""


def empty_record() -> DayRecord:
    """The record the app boots on, and the one the canonical snapshot uses.

    Everything absent. Every surface must render a NAMED REFUSAL against this —
    no crashes, no blanks, no zeros. That assertion is this slice's whole point.
    """
    return DayRecord()

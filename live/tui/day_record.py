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
class StreamMetrics:
    """**080.** One `keepUpToDate` stream's own numbers — symbol and sector
    tracked **separately, never pooled** (080 Part 4): a dead sector stream
    must not hide behind a healthy symbol stream in an average.

    `last_update_at`/`gaps_s` are `time.monotonic()` seconds, matching
    `_PacingGuard`'s and `cooldown_remaining_s`'s own clock convention —
    never wall time, which a session boundary or a DST change can jump.
    """

    label: str = ""
    update_count: int = 0
    last_update_at: Optional[float] = None
    #: Capped so this cannot grow unbounded across a long session — the
    #: distribution's shape is the point (008b: median 5.002s, max 14.477s),
    #: not a lifetime log.
    gaps_s: list = field(default_factory=list)
    error: str = ""


@dataclass
class RequestMetrics:
    """**080 Part 4.** One historical request's own numbers."""

    role: str = ""
    wall_s: Optional[float] = None
    bars_received: Optional[int] = None
    #: `None` where an expected count is not computable from duration/bar
    #: size alone (080 Part 0: "nothing you write may imply a certainty
    #: the measurement does not have") — rendered absent rather than guessed.
    bars_requested: Optional[int] = None
    error: str = ""


@dataclass
class AttachMetrics:
    """**080 Part 4.** Recorded, never rendered on ATTACHED — HEALTH renders
    it. Per-stage keypress-to-paint, per-stream update stats, per-request
    wall time and bar counts."""

    stage1_keypress_to_paint_s: Optional[float] = None
    stage2_first_row_s: Optional[float] = None
    stage2_last_row_s: Optional[float] = None
    streams: dict = field(default_factory=dict)     # {"symbol": StreamMetrics, "sector": StreamMetrics}
    requests: dict = field(default_factory=dict)     # {"rth_dailies": RequestMetrics, ...}


@dataclass
class Attached:
    """One attached symbol, **and the context block that was measured for it.**

    **080: two stages, not one.** `context`/`rail` are populated
    INCREMENTALLY now — `app.py` merges each row in as it lands
    (`compute_context_and_rail`), so a key's absence from `context` while
    `since` is already set is the **pending** state, not an omission. A row
    is never removed once landed; it can only be replaced by a fresher
    computation of itself.

    **These are `Measured`s, not strings.** `render_panels` is a pure function of
    this record and formatting is its job; storing pre-rendered rows here would
    put the refusal grammar in two places, and `grammar.py` exists so that it is
    in one.
    """

    symbol: str
    since: str = ""
    #: **080.** The sector ETF symbol (or `""`), carried alongside `context`
    #: so `RVOL`'s row can label its second reading `vs XLK` rather than a
    #: generic `vs sector` — the render layer needs the STRING, not just
    #: whether a mapping exists.
    sector_etf: str = ""
    #: **083.** `"rth"`/`"eth"`, derived from the SAME `SessionBasis`
    #: instance `Stage2Inputs.rvol_basis` carries — set once, at stage-1
    #: landing, because the anchor is a fact about the row known at attach,
    #: not about a value that has landed yet (renders even while `RVOL` is
    #: still `pending`).
    rvol_anchor: str = ""
    #: ADR, extension, VWAP, cum vol, both RVOL readings. Merged in row by
    #: row as `compute_context_and_rail` produces them — see the class note.
    context: dict = field(default_factory=dict)
    #: PDH/PDL, PMH/PML, ORH/ORL, VWAP, 52-week, rounds. Merged in once
    #: `rth_dailies` lands (`compute_context_and_rail` returns it as a whole
    #: — the rail has no per-row landing requirement of its own).
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
    #: **080 Part 3.** The freshness clock lives on `metrics.streams["symbol"
    #: /"sector"].last_update_at` — ONE source of truth for both "how fresh"
    #: and "how many updates/what gap distribution" (080 Part 4), rather than
    #: a second copy of the same timestamp. Exactly two independently-aged
    #: streams — task 080's own text: "two streams, two independent ages" —
    #: never per-row, because `Last $`/`VWAP`/`ADR% used`/`RVOL`'s own
    #: reading all read the SAME symbol stream, and `RVOL`'s sector-relative
    #: reading alone reads the sector stream.
    metrics: AttachMetrics = field(default_factory=AttachMetrics)


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

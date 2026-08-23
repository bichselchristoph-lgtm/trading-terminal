"""The TUI frame — S009 §4b, §4d, §4e, §4g, §4h; S009a parts 1 and 3.

**Tiled, not switchable.** Watchlist, attached symbol and tape across the top;
sizing, risk and health along the bottom. Nothing hidden, nothing switched.
`Ctrl+Tab` rotates focus and **is the entire navigation surface**; `a` opens the
attach prompt. No window management, no screen switching, no drag-and-drop.

**This docstring used to claim `Ctrl+P` is the palette for the long tail, and no
palette was ever registered** (032). `Ctrl+P` opens Textual's own built-in
palette, carrying theme and quit — nothing this application put there. The claim
is deleted rather than implemented: 032 asks for the smallest way in, and a
command palette with one command in it is a command system, which that task
forbids in the same sentence. **The sentence is recorded here rather than simply
removed** — a mechanism named in prose with no implementation is §7, and the
third instance of it in this repo; deleting the evidence quietly is how the
fourth one gets written.

**`render_panels(record)` is a PURE FUNCTION of the day record.** No panel
reaches around it to compute anything. Everything downstream leans on that, and
retrofitting it later costs ten times as much.

Colour, and what it may never say (§4h):

* **Green renders nowhere.** It is reserved for a fitted signal measured against
  a pre-registered outcome, and nothing in this system is fitted.
* **Red-inverse is reserved for exactly one badge**, `[ STOPPED — DAILY LIMIT ]`.
* **Dim-inverse for refusals** — absence is not failure.
* Blue is a fact about config, never about the market.
* No verdict colour, no letter grades, no state names, no detector polarity.
  `_state_cell`'s polarity argument is **deleted, not conditioned** — it does not
  exist in this module.
* **Status is encoded by position and typography, never colour alone**, so it
  survives 16-colour degradation over SSH.

----

**S009a — the panel is measured against the space it is actually given.**

S009 shipped at 99 passed / 0 failed and broke on the machine Christoph trades
on. One root cause produced all three defects: **nothing compared the panel to
its tile.**
`BOX_WIDTH` was compared against nothing, the caption was appended after the
border was sized, and the too-small guard measured the *window* while the thing
that overflows is the *tile*.

So the invariant is now stated once and enforced everywhere below it:

    Every width-dependent thing is computed from the width the tile actually
    received. Nothing renders at a width it was not measured against.

`BOX_WIDTH` survives as **the width the panel is designed at and every snapshot
is taken at** — not the width it renders at. `Panel.body(width, height)` takes
both dimensions; `on_resize` feeds it the real ones. The minimum is **derived
from each panel's own content** (`Panel.min_width`/`min_height`) rather than
chosen, because a fixed 60×16 is exactly what let a 1920 window split three ways
pass a check while every tile was far under what it needed.
"""
from __future__ import annotations

import asyncio
import functools
import os
import re
import sys
import unicodedata

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static

# **The import 032 found missing.** `live/attach/attach.py` existed with 18kB of
# tests against it and NOTHING in the running application imported it. The three
# local imports below were the whole of this module's reach, and `attach` was not
# among them — which is the finding stated as a line of code.
from ..attach.attach import MarketData, attach
# **034: the import that was missing one layer down.** `live/attach/ibkr.py` —
# the only module in this tree that touches a broker — was imported by nothing
# at all, not even a test, while 032 was fixing the same shape for `attach()`.
from ..attach.ibkr import IbkrConfig, connect
from .day_record import Attached, DayRecord, empty_record
from .grammar import Cell, FLAGGED_NOT_ERROR
from .layout import Layout
from .numbers import NO_BASIS, basis_label, format_value, needs_basis

#: Session logic is US/Eastern via `zoneinfo`, never machine locale — the
#: workspace convention, applied to the one clock this module reads.
EASTERN = ZoneInfo("America/New_York")

#: The key that opens the attach prompt.
#:
#: **A constant, not a setting, and that is the §4.4 answer rather than a dodge.**
#: §4.4 forbids a setting acquiring a default at a boundary. A key declared in
#: `config/layout.yaml` with a fallback here would be exactly that; a key with no
#: fallback would make a missing config line fatal to a terminal that otherwise
#: works. So it is not configurable, which is a decision this comment records.
#:
#: **Written once, and `BINDINGS` is the only reader.** 032's third constraint is
#: *not a literal in two places* — the moment a second site spells `"a"`, the key
#: and the thing describing it can disagree and nothing would notice.
ATTACH_KEY = "a"

#: §4d — the width the panel is DESIGNED at, and the width every snapshot is
#: taken at. **Not the width it renders at.** The mockups were 69–71 chars
#: against a 71-char border: invisible in HTML, visibly broken in a console.
BOX_WIDTH = 71

#: `padding: 0 1` in the CSS below costs each tile two columns. It is named here
#: because the too-small guard has to subtract it — S009's guard did not, which
#: is half of why a border two columns too wide wrapped instead of refusing.
TILE_PADDING = 2

#: How much of the caption must survive for a panel to be worth rendering at
#: all. §4d: *a live panel with no update stamp is the `[ STALE ]` anti-state* —
#: so the floor is the shortest provenance that still says something, plus the
#: ellipsis that renders the loss. Below this the panel refuses rather than
#: rendering a stamp nobody can read.
PROVENANCE_STUB = 6


def display_width(s: str) -> int:
    """Account for ambiguous-width `·` and `—` (§4d).

    `unicodedata.east_asian_width` returns 'A' (ambiguous) for both. A terminal
    may render them one or two columns wide; we count them as ONE, which is what
    every terminal tested here does, and the border test pins the result so a
    wrong assumption fails loudly rather than drifting.
    """
    return sum(2 if unicodedata.east_asian_width(ch) == "W" else 1 for ch in s)


def ascii_safe() -> bool:
    """§4d — ASCII fallback.

    The spec names ONE trigger: `SSH_CONNECTION`. **That is not sufficient, and
    this was found on first render rather than reasoned about.** A Windows
    console on cp1252 raises `UnicodeEncodeError` on `┌` and `─` with no SSH
    involved at all — the box-drawing characters are simply unencodable, and the
    app dies rather than degrading.

    So the trigger is widened to *"the output encoding cannot carry the
    characters"*, which is the property §4d actually cares about; SSH was one
    cause of it, not the condition itself. Recorded in the done-note as a spec
    amendment rather than applied silently.
    """
    if os.environ.get("SSH_CONNECTION"):
        return True
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    if not enc:
        return True
    try:
        "┌─·—".encode(enc)
    except (UnicodeEncodeError, LookupError):
        return True
    return False


def fit(s: str, width: int) -> str:
    """Truncate to `width` **rendering the loss**, never silently.

    S009a 1a: *"truncate or drop by a declared rule that renders the loss, never
    by silent overflow."* Silent overflow is what shipped — the terminal wrapped
    the surplus onto the next line, which turns one provenance stamp into two
    lines of debris and reads as a rendering fault rather than as a panel that
    was given too little room.

    The ellipsis is part of the budget, so the result is never wider than
    `width`. That matters more than it looks: this function is the last thing
    every line passes through, and it is what makes *"nothing renders at a width
    it was not measured against"* true rather than intended.
    """
    if display_width(s) <= width:
        return s
    ell = "..." if ascii_safe() else "…"
    if width <= display_width(ell):
        return ell[:max(width, 0)]
    keep, out = width - display_width(ell), ""
    for ch in s:
        if display_width(out) + display_width(ch) > keep:
            break
        out += ch
    return out + ell


def _label(row: str) -> str:
    """The naming half of a pinned row — everything before its value.

    Split on the first run of **two or more** spaces, which is how every pinned
    row in this module separates its label from its cell. **Derived from the row
    itself**, so a panel's minimum width is a property of its own content rather
    than a number somebody picked; that is the whole difference between this and
    the `60×16` it replaces.
    """
    return re.split(r"\s{2,}", row.strip(), maxsplit=1)[0]


def too_small_message(cols: int, rows: int, min_cols: int, min_rows: int,
                      per_tile: str = "") -> str:
    """§4e/§5 — a STATED refusal, never a silently clipped panel.

    It narrows to exactly ONE meaning: the pinned rows do not fit. Not "the
    layout is awkward", which is a different statement and would make the
    message useless for deciding anything.

    `per_tile` carries **which tile ran out and by how much**, because the
    window figure alone was what made S009's guard useless — a 1920 window
    satisfies any window minimum while each of its three tiles is starved.
    """
    base = (f"window too small - the pinned rows do not fit "
            f"({cols}x{rows}, need {min_cols}x{min_rows})")
    return f"{base}  [{per_tile}]" if per_tile else base


def box_top(title: str, provenance: str, width: int = BOX_WIDTH) -> str:
    """§4d — the RIGHT-HAND END of every top border carries provenance.

    Source, as-of time, sample window, or safety state. **A live panel with no
    update stamp is the `[ STALE ]` anti-state**, so `provenance` is not
    optional — callers pass a refusal string when they have nothing.

    **The caption gives way; the title never does** (S009a 1a). The title is what
    identifies which tile you are looking at, and a panel you cannot name is
    worse than a panel whose as-of time is abbreviated — you can still ask what
    the stamp said, but not which panel asked it. So the provenance truncates
    from its right with a visible ellipsis, and the final `fit` guarantees the
    line is exactly `width` even in the degenerate case where the title alone
    overruns.
    """
    h, tl, tr = ("-", "+", "+") if ascii_safe() else ("─", "┌", "┐")
    left = f"{tl}{h} {title} "
    if width - display_width(left) - display_width(f" {provenance} {tr}") < 1:
        # Budget: one rule character, two spaces and the corner all survive, so
        # the caption gets `width - left - 4`. Anything larger leaves the line a
        # column over and the FINAL fit eats the corner instead of the caption
        # — a double truncation that renders `not atta……` with no `┐`, which is
        # the caption giving way twice and the border giving way once.
        provenance = fit(provenance, max(width - display_width(left) - 4, 1))
    right = f" {provenance} {tr}"
    pad = width - display_width(left) - display_width(right)
    line = left + (h * max(pad, 1)) + right
    return line if display_width(line) <= width else fit(line, width)


class Panel(Static):
    """One tile. Renders rows, and says so when there are more below (§4e).

    ***"Nothing more here"* and *"more below"* must not render identically.**
    A limit breach at row 19 of a 12-row viewport is indistinguishable from no
    breach — the sixth instance in this project of a correct warning nobody was
    instructed to read.

    **S009a: the tile's real width and height are the inputs.** `viewport` is
    now a fallback for the pure/snapshot path only; when a height is supplied it
    is measured, so a panel given eight lines shows what fits in eight and says
    how many it could not show, rather than being clipped by the layout with no
    trace. That is the same rule as §4e applied to the dimension nobody checked.
    """

    def __init__(self, title: str, provenance: str, rows: list[str],
                 pinned: list[str] | None = None, viewport: int = 8) -> None:
        self.title_text = title
        self.provenance = provenance
        self.rows = rows
        self.pinned = pinned or []
        self.viewport = viewport
        super().__init__(self.body())

    # ---- what this panel needs, derived from what it holds -----------------

    def chrome(self) -> int:
        """Lines this panel spends on anything that is not a scrolling row."""
        return (1                                      # top border
                + (1 if self.rows else 0)              # the `N of M` line
                + ((1 + len(self.pinned)) if self.pinned else 0))

    def min_width(self) -> int:
        """**Derived, never fixed.** Two things may not give way.

        The **title plus a provenance stub**, because §4d makes an unstamped
        panel the `[ STALE ]` anti-state — a border with no legible caption is
        not a narrower panel, it is a different and worse one.

        Every **pinned row's label**, because §4e's pinned band exists so a
        failed rule survives scrolling. A pinned row truncated past its label is
        a failed rule that renders as punctuation.
        """
        # +4 is `box_top`'s own budget: one rule character, two spaces, one
        # corner. It must match, or the derived minimum admits a width at which
        # the caption is cut below its stub.
        frame = display_width(f"+- {self.title_text} ") + PROVENANCE_STUB + 4
        pinned = max((display_width("  " + _label(p)) + 1 for p in self.pinned),
                     default=0)
        return max(frame, pinned)

    def min_height(self) -> int:
        """Chrome plus one scrolling row. Below this there is nothing to read —
        `N of M · +K more` on its own is a panel reporting that it is a panel."""
        return self.chrome() + (1 if self.rows else 0)

    # ---- rendering ---------------------------------------------------------

    def body(self, width: int = BOX_WIDTH, height: int | None = None) -> str:
        rule = "-" if ascii_safe() else "─"
        out = [box_top(self.title_text, self.provenance, width)]
        viewport = self.viewport if height is None else max(1, height - self.chrome())
        shown = self.rows[:viewport]
        out += [fit(r, width) for r in shown]
        hidden = len(self.rows) - len(shown)
        if hidden > 0:
            # Both halves of §4e: the count in the caption AND the edge marker.
            out.append(fit(f"  {len(shown)} of {len(self.rows)} · +{hidden} more ↓", width))
        elif self.rows:
            out.append(fit(f"  {len(self.rows)} of {len(self.rows)} · end", width))
        if self.pinned:
            # §4e — sticky band. Risk rows, limit rows, failed rules and active
            # refusals survive scrolling; without this the pinning rule is prose.
            out.append("  " + rule * max(width - 4, 1))
            out += [fit(f"  {p}", width) for p in self.pinned]
        return "\n".join(out)

    def _body(self) -> str:
        """The design-width render. Every snapshot and border test is taken
        here, so `BOX_WIDTH` keeps meaning exactly what it meant."""
        return self.body()

    def on_resize(self) -> None:
        """The whole of S009a 1a and 1b, in three lines.

        `content_size` excludes `padding`, so this is the space the text really
        has. Falling back to `size` keeps the panel rendering if a future style
        change removes the padding.
        """
        w = self.content_size.width or self.size.width
        h = self.content_size.height or self.size.height
        if w:
            self.update(self.body(w, h or None))


#: The order the context block renders in, and it is **the order the numbers are
#: used in**, not alphabetical: the range budget first, because ADR is what says
#: whether there is room left in the day at all; then the SMA extensions; then
#: today's session. A dict's insertion order would work until `_context_block`
#: was reordered for an unrelated reason, so the screen declares its own.
CONTEXT_ORDER = ("ADR%", "ADR%avail", "ATR20",
                 "ext 10", "ext 20", "ext 50", "VWAP", "cum vol", "RVOL",
                 "RVOL_rel")

#: The level rail. **`VWAP` is deliberately absent** — `level_rail` carries it
#: and so does the context block, and rendering one value twice is how two rows
#: come to disagree after somebody fixes one of them.
RAIL_ORDER = ("PDH", "PDL", "PMH", "PML", "ORH5", "ORL5", "ORH15", "ORL15",
              "52wH", "52wL", "round")


def measured_cell(m) -> str:
    """A `Measured` through the refusal grammar.

    **`sample` rides with the number** — S010 requires it on every rendered
    value, and a bare `2.00` is a value with nothing behind it, which is the
    thing tenet 2 and this whole module exist to prevent. An absent `Measured`
    already names its own reason, so it goes through `Cell.absent` and renders
    `— (need 21 daily bars, have 5)` rather than a blank.
    """
    if not getattr(m, "ok", False):
        return Cell.absent(getattr(m, "unavailable", "") or "absent").render()

    # **A value with no declared basis REFUSES.** 038's exit test, and it is a
    # refusal rather than a blank label on purpose: an unlabelled number on this
    # panel is the whole defect 038 exists to close. ADR and ATR sit four rows
    # apart, are both labelled volatility, and are computed on different sessions
    # deliberately — a reader who cannot see that compares them.
    if needs_basis(m) and basis_label(m) is None:
        return Cell.absent(NO_BASIS).render()

    text = Cell.value(format_value(m)).render()
    # **Basis last, after the sample.** The sample says what it was computed
    # OVER — `20 sessions, excl. today` — and the basis says WHICH BARS those
    # sessions were, which is the qualifier on everything before it.
    detail = " · ".join(x for x in (m.sample, basis_label(m)) if x)
    return f"{text}  · {detail}" if detail else text


def _as_of_clock(ts: str) -> str:
    """Today's as-of renders as a clock; any other day keeps its date.

    **The date is dropped only when dropping it cannot mislead.** The stamp row
    is ~72 characters with a full timestamp against a ~62-column tile, so `fit`
    was truncating `lag` off the end — losing the one number that says how stale
    the block is, which is precisely the value §4d refuses to let give way. But a
    bar from LAST session rendered as a bare `16:00` would read as an hour ago,
    so the date survives whenever it is not today's.

    The record keeps the full timestamp either way; this is the renderer's
    decision and lives with the rest of the formatting.
    """
    today = datetime.now(EASTERN).strftime("%Y-%m-%d")
    if ts.startswith(today):
        return ts[11:16] or ts
    return ts


def context_rows(a: Attached) -> list[str]:
    """The context block for one attached symbol. 034 part 4.

    **Indented one level under its symbol**, because the panel holds a list of
    attachments and a flat block would read as belonging to whichever symbol the
    eye landed on last.

    **The stamp is BLOCK-LEVEL, and that is a limitation this function cannot
    fix.** §3 and the third tenet want source, as-of and lag on every value;
    `Measured` carries `value`, `sample` and `unavailable` and has no field for
    an as-of or a lag. So one stamp covers the block, each row carries its own
    `sample`, and the gap is recorded in the done-note rather than papered over
    with a stamp computed at render time — which would say when the SCREEN was
    painted, not when the DATA was true, and would be a well-formed value
    answering a different question.
    """
    if not a.context and not a.rail:
        return [f"    {Cell.not_yet('no context block measured').render()}"]
    stamp = " · ".join(x for x in (
        a.source,
        f"as of {_as_of_clock(a.as_of)}" if a.as_of else "",
        f"lag {a.lag}" if a.lag else "") if x)
    rows = [f"    {'from':<9} {stamp}" if stamp
            else f"    {'from':<9} {Cell.absent('no source recorded').render()}"]
    if a.slot_state:
        rows.append(f"    {'slot':<9} {a.slot_state}")
    if a.tape:
        rows.append(f"    {'tape':<9} {a.tape}")
    if a.partial:
        # **058 Part 3.** A screen-level statement that the gather completed
        # with refusals — tenet 3 (status inherits from the weakest),
        # rendered rather than merely true. `flagged, not an error`: the
        # attach itself did not fail, some of its rows did, and those rows
        # already say why individually below.
        rows.append(f"    {'':<9} {Cell.degraded(a.partial, FLAGGED_NOT_ERROR).render()}")
    for name in CONTEXT_ORDER:
        if name in a.context:
            rows.append(f"    {name:<9} {measured_cell(a.context[name])}")
    for name in RAIL_ORDER:
        if name in a.rail:
            rows.append(f"    {name:<9} {measured_cell(a.rail[name])}")
    return rows


def render_panels(record: DayRecord, layout: Layout) -> dict[str, Panel]:
    """PURE. Day record in, panels out. Nothing else is consulted.

    Every panel renders a NAMED REFUSAL on an empty record — no blanks, no
    zeros, no crashes.
    """
    p: dict[str, Panel] = {}

    wl = record.tickets
    p["watchlist"] = Panel(
        "WATCHLIST", "no ingest today" if not wl else "ingest · today",
        [f"  {t.symbol}  {t.state}" for t in wl]
        or [f"  {Cell.absent('no watchlist ingested today').render()}"])

    at = record.attached
    # **A refusal renders alongside what is attached, not instead of it** (032,
    # `SPEC.md` §4.2 — surfaced, not refused). A failed attach must not blank a
    # symbol that is working: those are two independent facts and collapsing them
    # would make one bad ticker look like a disconnection.
    attach_rows: list[str] = []
    for a in at:
        attach_rows.append(f"  {a.symbol}  attached {a.since}")
        attach_rows += context_rows(a)
    # **058 Part 3 — the atomic swap.** The outgoing symbol's row is already
    # gone from `record.attached` by the time this renders (`_begin_attach`
    # removes it before the worker even starts), so there is nothing here to
    # blend with the badge below. One screen-level state, not a per-cell
    # pending state — `BUILD-PLAN` slice 010 §7 wins over §3's retired
    # `fetching dailies…`.
    if record.attaching:
        attach_rows.append(f"  {Cell.attaching(record.attaching).render()}")
    if record.attach_refusal:
        attach_rows.append(f"  {Cell.absent(record.attach_refusal).render()}")
    if record.attaching:
        provenance = Cell.attaching(record.attaching).render()
    elif not at:
        provenance = "not attached"
    else:
        provenance = f"since {at[0].since}"
    p["attached"] = Panel(
        "ATTACHED", provenance,
        attach_rows or [f"  {Cell.absent('nothing attached').render()}"])

    p["tape"] = Panel(
        "TAPE", "no source",
        [f"  {Cell.no_source('no tape subscription in this slice').render()}"])

    p["sizing"] = Panel(
        "SIZING", "not transmitted",
        [f"  1R        {Cell.absent('no account snapshot').render()}",
         f"  shares    {Cell.absent('no entry, no stop').render()}"],
        pinned=[f"risk      {Cell.absent('no account snapshot').render()}"])

    p["risk"] = Panel(
        "RISK", "not transmitted",
        [f"  day P&L   {Cell.absent('no trades today').render()}",
         f"  open R    {Cell.absent('no positions').render()}"],
        pinned=[f"daily limit  {Cell.not_yet('no account snapshot').render()}"])

    h = record.health
    ratio = (f"{h.frames_painted}/{h.ticks_received}"
             if h.ticks_received else Cell.not_yet("no ticks received").render())
    # 034 part 3 — **three states, and they must not render alike.** Connected
    # names the endpoint and the client. Refused names the endpoint and WHY.
    # Neither means nothing ever tried, which is what an empty record is and is
    # a different fact from a connection that was attempted and failed.
    #
    # **The endpoint and its state are on SEPARATE ROWS, and that is measured
    # rather than stylistic.** On one row the cell is
    # `— (IBKR 127.0.0.1:7496 not connected - connection refused)`, 58 columns
    # against the ~56 a HEALTH tile has at 209x54 — so `fit` truncated the
    # REASON and left the endpoint, which is the half you can already guess.
    # §4d says the caption gives way and the title never does; the same rule
    # applied here says the endpoint may wrap and the reason may not vanish.
    source_rows: list[str] = []
    for name, state in sorted(h.sources.items()):
        source_rows.append(f"  {'sources' if not source_rows else '':<9} {name}")
        source_rows.append(f"  {'':<9} {state}")
    for name, why in sorted(h.unavailable_sources.items()):
        source_rows.append(f"  {'sources' if not source_rows else '':<9} {name}")
        source_rows.append(f"  {'':<9} {Cell.no_source(why).render()}")
    if not source_rows:
        source_rows = [f"  sources   {Cell.no_source('no feed connected').render()}"]
    last_seen_rows = ([f"  last seen {Cell.absent('nothing seen').render()}"]
                      if not h.last_seen else
                      [f"  last seen {n}  {t}" for n, t in sorted(h.last_seen.items())])
    p["health"] = Panel(
        "HEALTH", "updates · none yet",
        source_rows + last_seen_rows + [f"  frames/ticks  {ratio}"],
        pinned=[f"regime    {Cell.not_built().render()}"
                if not record.regime_snapshot.ref
                else f"regime    {record.regime_snapshot.ref}"])

    p["pipeline"] = pipeline_panel(layout)
    return p


def pipeline_panel(layout: Layout) -> Panel:
    """S009a part 3 — the absence that had to be asked about.

    Christoph asked whether there should be an indicator section. There should,
    and **nothing on screen said so.** A stage absent from `config/layout.yaml`
    did not render at all, so *"this stage is not built yet"* and *"this stage
    does not exist in the design"* were the same picture. Same shape as
    *"nothing more here"* versus *"more below"*, and it is the Layer 0 failure
    inverted: Layer 0 rendered as built when it was not; this rendered as
    nothing when it was merely not yet.

    So all twelve stages render, and an unbuilt one **names the slice that will
    fill it**. The empty screen becomes a build progress report.

    **`NOT BUILT` and a data-absent refusal are structurally different, without
    colour** (Refusal C): a badge in brackets, `[ NOT BUILT · S010 ]`, against an
    em-dash and a parenthesised reason, `— (no account snapshot)`. One says the
    machinery does not exist; the other says the machinery exists and the input
    is missing. Collapsing those would be the defect this task is fixing.
    """
    stages = layout.stages
    rows, built = [], 0
    for s in stages:
        if s.renders:
            # `regime` is NOT a stage that is coming — SPEC.md §3.2 removes every
            # regime layer from the terminal, and it is produced by the scheduled
            # Claude task. The health panel's pointer is correct and must not
            # become a NOT BUILT panel; this row points at it instead.
            cell = f"{'->' if ascii_safe() else '→'} {s.renders} panel"
            built += 1
        elif s.human:
            # Not a slice and never will be. A stage the system does not perform
            # must not render as one it has not performed yet — and it must not
            # read like `manage`, which IS missing a slice. "Correctly" carries
            # that distinction; without it the two absences look identical.
            cell = "your decision - correctly not a slice"
        elif s.deferred:
            # 018 part 4. **Ruled on and postponed is not the same as nobody
            # decided**, and the screen was making the weaker claim.
            #
            # NO NEW BADGE WORD. `[ DEFERRED ]` is not in SPEC.md §4's
            # vocabulary, and grammar.py states that a new one is a spec change
            # rather than a code change. So the badge stays `[ NOT BUILT ]` --
            # which is true, the machinery does not exist -- and the ruling goes
            # in the reason, where the difference from `slice not assigned` is
            # carried by words rather than by an invented token.
            cell = Cell.not_built(reason=f"deferred - {s.deferred}").render()
        elif s.built_by:
            cell = f"built - {s.built_by}"
            built += 1
        else:
            cell = Cell.not_built(reason="" if s.slice else "slice not assigned",
                                  slice_id=s.slice).render()
        rows.append(f"  {s.slot:>2} {s.name:<11} {cell}")
    return Panel("PIPELINE", f"{built} of {len(stages)} built", rows,
                 viewport=len(stages) or 1)


class Frame(Vertical):
    """Holds either the refusal or the tiles, and **re-decides on every resize.**

    The handler lives here rather than on the app because Textual dispatches
    `Resize` to widgets, not to `App` — putting it on the app looks right, runs
    never, and leaves the guard exactly as launch-only as the one 018 part 2 is
    fixing. Found by the resize test failing with `NoMatches` on `#too-small`.
    """

    async def on_resize(self) -> None:
        await self.app._apply_fit()


class MomentumApp(App):
    """The frame. Boots on an empty record and refuses, visibly, everywhere."""

    CSS = """
    Screen { layout: vertical; }
    .row { height: 1fr; }
    Panel { border: none; padding: 0 1; width: 1fr; }
    /* One line, docked, no border. The prompt is transient and must not change
       what the too-small guard measured — a three-line bordered Input would take
       a fifth of an 16-row window away from the tiles it already checked. */
    #attach-input { dock: bottom; height: 1; border: none; padding: 0 1; }
    """
    BINDINGS = [
        ("ctrl+tab", "focus_next", "Next panel"),
        # **The whole of 032, as one line.** `attach()` shipped complete, tested
        # at 18kB and reachable from nothing. There was no key, no action, no
        # palette entry and no command — the only way to run it was to import it
        # from a test.
        (ATTACH_KEY, "attach", "Attach a symbol"),
        # A prompt with no way out is a trap, and the cost of not having this is
        # a terminal you kill from another window. Textual's `Input` does not
        # bind `escape`, so it bubbles here.
        ("escape", "cancel_attach", "Cancel"),
    ]

    def __init__(self, record: DayRecord | None = None, layout: Layout | None = None,
                 md: MarketData | None = None):
        """`md` is the market data the attach path is allowed to ask (S010).

        **It defaults to `None` and that is a state, not an omission.** Until 034
        it was also the only state anyone could reach: `main()` constructed no
        client, so `md` was `None` for every person who ran the program. **That
        is no longer true** — `main()` now builds an `IBKRMarketData` from
        `config/ibkr.yaml` — but `None` remains a first-class state, because a
        refused connection reaches exactly this branch. With `md` absent the
        attach prompt still opens, still accepts a symbol, and renders a NAMED
        refusal saying what is missing. `SPEC.md` §4.2: an unreachable feature
        and a feature that says why it cannot run are not the same screen.
        """
        self.record = record if record is not None else empty_record()
        self.layout_cfg = layout or Layout.load()
        self.md = md
        #: `060` — `_apply_fit` is check-then-act ("no `Panel` mounted? mount
        #: one") and is reachable from two independent callers: `_rerender()`
        #: (the attach path) and `Frame.on_resize`. Nothing serialised them, so
        #: a resize landing between one call's `remove_children()` and its own
        #: `mount()` let a second call see the same empty frame and mount a
        #: second full panel set beside the first — `B-001`, reproducing at
        #: 120x40 roughly one attach cycle in five. The lock makes the
        #: check-and-mount one atomic step regardless of which caller triggers it.
        self._fit_lock = asyncio.Lock()
        super().__init__()

    @property
    def source_name(self) -> str:
        """The connected feed, named — for stamping an attached context block.

        **Read off the day record rather than held as a second field.** The
        launcher already put it there for HEALTH to render, and a constructor
        argument carrying the same string would be the two-places defect with
        the copies one attach apart.
        """
        return next(iter(sorted(self.record.health.sources)), "")

    # ---- attaching a symbol, 032 -------------------------------------------

    async def action_attach(self) -> None:
        """Open the prompt. **One line of input, and nothing else.**

        Re-pressing the key while it is open focuses the existing prompt rather
        than mounting a second one — two inputs stacked at the bottom would both
        accept a symbol and only one of them would be read.
        """
        existing = self.query("#attach-input")
        if existing:
            existing.first(Input).focus()
            return
        prompt = Input(placeholder="symbol to attach  (enter to attach, esc to cancel)",
                       id="attach-input")
        await self.mount(prompt)
        prompt.focus()

    async def action_cancel_attach(self) -> None:
        await self._close_prompt()

    async def _close_prompt(self) -> None:
        for widget in self.query("#attach-input"):
            await widget.remove()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit — the only place a typed symbol becomes an attach.

        **058 Part 3: the freeze fix.** `attach()` blocks on IBKR round trips
        even after Part 2's concurrent dispatch — Part 2 shrinks the window,
        it does not remove it. So the actual call runs on a Textual worker
        thread; this coroutine only does the ATOMIC SWAP's first step (drop
        the outgoing symbol's values, declare `ATTACHING`) and returns —
        the UI stays responsive for the whole of the gather, which is
        `test_the_ui_stays_responsive_during_an_attach` in
        `live/tests/test_attaching_state.py`.

        `md is None` is the one case with no network to wait on — it renders
        synchronously rather than round-tripping through a worker for
        nothing.
        """
        typed = event.value.strip()
        await self._close_prompt()
        if not typed:
            return
        symbol = typed.strip().upper()
        if self.md is None:
            self.record.attaching = ""
            self.record.attached = [a for a in self.record.attached
                                    if a.symbol != symbol]
            self.record.attach_refusal = (
                f"{symbol}: no market data - the app connects to "
                "no broker in this slice")
            await self._rerender()
            return
        self._begin_attach(symbol)
        await self._rerender()
        self.run_worker(functools.partial(self._attach_worker, symbol),
                        thread=True, exclusive=False, group="attach",
                        name=f"attach-{symbol}")

    def _begin_attach(self, symbol: str) -> None:
        """**058 Part 3, the atomic swap's first step.** Every value
        dependent on the outgoing symbol is dropped immediately — not left
        on screen, not greyed. `ATTACHED` §6b.5 rules that a DETACHED symbol
        renders `STALE`; this is a RE-ATTACH of the same symbol (or a fresh
        one), and a value from the previous attach sitting under the new
        header while the new one is still in flight is the §7 archetype: a
        well-formed value answering a different question."""
        self.record.attached = [a for a in self.record.attached
                                if a.symbol != symbol]
        self.record.attach_refusal = ""
        self.record.attaching = symbol

    def _attach_worker(self, symbol: str) -> None:
        """**Runs OFF the Textual event loop thread.** Computes only — the
        record is mutated back on the MAIN thread via `call_from_thread`,
        because `self.record` is read by `_apply_fit`/render calls that can
        run concurrently with this thread, and Textual is explicit that its
        own objects are not thread-safe to touch from here.

        032's first constraint still holds: *the binding calls
        `live.attach.attach()` and does not reimplement any of it.* Every
        string below is either `AttachResult`'s or names the one thing
        `AttachResult` cannot know, which is that no `MarketData` exists —
        and that branch is handled in `on_input_submitted` before a worker is
        ever started, so it cannot appear here.

        **A bare worker thread has no asyncio event loop of its own, and
        `ib_async`'s dependency `eventkit` reads `asyncio.get_event_loop()`
        at IMPORT time.** Python's default policy raises on any non-main
        thread with no loop set — found live, the first time this path ran:
        `resolve()` rendered `contract lookup failed (RuntimeError)` naming
        `There is no current event loop in thread 'ThreadPoolExecutor-...'`,
        and because the failed import is never cached, EVERY later test in
        the same process (including ones with no worker at all) inherited
        the failure once the main thread's own loop slot was later spent by
        an unrelated `asyncio.run()`. Giving this thread a loop OBJECT (never
        run — `_BrokerLoop` is the loop that actually carries traffic) is
        enough to satisfy `eventkit` and let the import succeed once, cached,
        for the rest of the process.
        """
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            result = attach(symbol, self.md, origin="typed")
        except Exception as exc:                        # noqa: BLE001
            # `attach()` is documented to report rather than raise, but a
            # worker thread with an unhandled exception fails silently by
            # Textual's default — surfaced here rather than trusted away, so
            # a genuinely unexpected fault still renders instead of leaving
            # `ATTACHING` on screen forever (Refusal, never a stuck badge).
            self.call_from_thread(self._finish_attach, symbol, None,
                                  f"{symbol}: attach failed "
                                  f"({type(exc).__name__}: {exc})")
            return
        self.call_from_thread(self._finish_attach, symbol, result, None)

    async def _finish_attach(self, symbol: str, result, worker_refusal: Optional[str]) -> None:
        """**058 Part 3, the atomic swap's last step: every value lands in
        ONE paint.** Runs on the main thread (via `call_from_thread`), so
        this and `_begin_attach` are the only two places that mutate
        `record.attached`/`record.attaching` — there is no window where a
        reader of `self.record` sees a half-applied result.

        **Partial failure must not look like success.** `result.partial`
        (set by `attach()` when the gather completed with some rows
        refusing) rides onto `Attached` unchanged; `context_rows` renders it
        as a screen-level line beside the per-row refusals, so four values
        and two refusals cannot read as a complete attach of an illiquid
        name.
        """
        self.record.attaching = ""
        if worker_refusal is not None:
            self.record.attach_refusal = worker_refusal
        elif not result.attached:
            # `AttachResult` already carries the failure — render it, do not
            # re-word it. Ambiguity in particular carries its candidate count,
            # and a shorter message would drop the number that makes it useful.
            self.record.attach_refusal = f"{result.symbol}: {result.refusal}"
        else:
            # An attach that failed at steps 2-5 is still an attach, so a
            # stale refusal from a previous attempt must not survive one.
            # `_begin_attach` already dropped this symbol's old row; this
            # guards the case where the SYMBOL TYPED differs from the one
            # `attach()` normalised to (defensive — `attach()` upper-cases
            # and strips, matching `on_input_submitted`, so this is a no-op
            # on the path that actually runs).
            self.record.attached = [a for a in self.record.attached
                                    if a.symbol != result.symbol]
            # **034: the context block is CARRIED, not recomputed and not
            # dropped.** `attach()` measured all of it one line ago and
            # until now every value was discarded here — the panel showed
            # that a symbol was attached and nothing about it.
            # `render_panels` is pure over the record, so a value the record
            # does not hold is a value that cannot render.
            as_of, lag = self._stamp(result)
            self.record.attached.append(
                Attached(symbol=result.symbol,
                        since=datetime.now(EASTERN).strftime("%H:%M"),
                        context=result.context, rail=result.rail,
                        source=self.source_name, as_of=as_of, lag=lag,
                        tape=result.tape, slot_state=result.slot_state,
                        partial=result.partial))
            self.record.attach_refusal = ""
        await self._rerender()

    def _stamp(self, result) -> tuple[str, str]:
        """As-of and lag for the block, **derived from the DATA, never the clock
        alone.** The as-of is the last session bar's own timestamp; the lag is
        now minus that. A stamp taken at render time would say when the screen
        was painted, which is exactly the reading this project is named for.

        Both are empty when there is no bar to read one from — `context_rows`
        then renders the stamp without them rather than inventing one.
        """
        vwap = result.context.get("VWAP")
        span = getattr(vwap, "sample", "") if vwap is not None else ""
        # `vwap_from_bars` ends its sample with `... · <first ts> to <last ts>`.
        # The last timestamp is the newest bar the feed gave us, which is the
        # only as-of the data actually supports.
        ts = span.rsplit(" to ", 1)[-1].strip() if " to " in span else ""
        if not ts:
            return "", ""
        try:
            when = datetime.fromisoformat(ts)
        except ValueError:
            # A timestamp we cannot parse is still worth rendering; a LAG we
            # cannot compute is not worth guessing.
            return ts, ""
        if when.tzinfo is None:
            when = when.replace(tzinfo=EASTERN)
        seconds = int((datetime.now(EASTERN) - when).total_seconds())
        # **Normalised to US/Eastern, and this was a live defect rather than a
        # precaution.** `IBKRMarketData._bars` passes `formatDate=2`, so IBKR
        # stamps every bar in UTC; the first live attach rendered
        # `as of 17:18 · lag 55s` at 13:18 ET. The lag was right and the clock
        # was four hours ahead of the session it belongs to — a well-formed
        # value answering a different question, beside a correct one.
        #
        # Session logic is US/Eastern via `zoneinfo`, never machine locale and
        # never the wire format. The conversion happens HERE, where the
        # timestamp becomes something a person reads.
        return (when.astimezone(EASTERN).strftime("%Y-%m-%d %H:%M:%S"),
                f"{seconds}s" if abs(seconds) < 3600 else f"{seconds // 60}m")

    async def _rerender(self) -> None:
        """Rebuild the tiles from the record. `_apply_fit` remounts when no
        `Panel` is present, so emptying the frame is the whole trigger."""
        frame = self.query_one("#frame", Frame)
        await frame.remove_children()
        await self._apply_fit()

    def tile_rows(self) -> list[list[Panel]]:
        """The tiling, as rows of tiles. One place, so the too-small guard and
        `compose` cannot disagree about what is on screen — S009's guard
        measured a shape the renderer did not use."""
        panels = render_panels(self.record, self.layout_cfg)
        visible = [c.id for c in self.layout_cfg.visible_only]
        rows = [("watchlist", "attached", "tape"),
                ("sizing", "risk", "health"),
                ("pipeline",)]
        return [[panels[i] for i in r if i in visible and i in panels] for r in rows]

    @staticmethod
    def required(rows: list[list[Panel]]) -> tuple[int, int, str]:
        """**The per-tile check, and the real bug S009a found.**

        S009 compared the *window* against a fixed `60×16`. A 1920 window split
        three ways satisfies that while each tile has far less than one panel
        needs, so the guard could not fire at the size that actually broke — and
        what rendered was the silently clipped panel the rule forbids.

        This measures **each tile against what its own panel needs**, which makes
        it resolution-independent: the answer is the same whether the columns
        came from a 1920 screen at one font or a 3440 screen at another.
        """
        need_cols = need_rows = 0
        worst = ""
        for tiles in rows:
            if not tiles:
                continue
            widest = max(t.min_width() for t in tiles)
            cols = len(tiles) * (widest + TILE_PADDING)
            if cols > need_cols:
                need_cols = cols
                name = next(t.title_text for t in tiles if t.min_width() == widest)
                worst = (f"{len(tiles)} tiles x {widest} cols for {name}"
                         f" + {TILE_PADDING} padding")
            need_rows += max(t.min_height() for t in tiles)
        return need_cols, need_rows, worst

    def compose(self) -> ComposeResult:
        """An empty frame. **The decision is NOT taken here** — 018 part 2.

        `compose()` runs ONCE, at startup. S009a's guard lived here, so it was
        correct at launch and never again: shrink the window afterwards and the
        panels truncated to `WATCHLIS...` instead of refusing. **A rule that
        holds only at launch is not the rule**, and truncation at 24 columns is
        technically honest and functionally unreadable — a panel you cannot read
        is not a degraded panel, it is a different one.

        So the frame is empty and `_apply_fit` fills it, on mount and on every
        resize.
        """
        yield Frame(id="frame")

    async def on_mount(self) -> None:
        await self._apply_fit()

    async def _apply_fit(self) -> None:
        """Switch between the refusal and the panels, **in both directions.**

        A one-way transition would be worse than what it replaces: a terminal
        that refuses once and never comes back is a terminal you restart, and
        restarting to recover from a resize teaches you not to resize.

        **The message is RECOMPUTED on every call, never reused.** A refusal
        naming the launch size while the window is now a different size is a
        well-formed value answering a different question — the defect this
        project is named for, rendered in the widget whose job is to prevent it.
        """
        cols, height = self.size.width or 0, self.size.height or 0
        if not (cols and height):
            return
        # `060` — everything from here on is check-then-act against the DOM
        # (`self.query(...)` then `frame.mount(...)`), and `_rerender()` and
        # `Frame.on_resize` both call this method. Without the lock, a resize
        # landing mid-remount let a second caller see the same "empty frame"
        # and mount a second full panel set. One lock, one mount decision.
        async with self._fit_lock:
            rows = self.tile_rows()
            need_cols, need_rows, worst = self.required(rows)
            frame = self.query_one("#frame", Frame)

            if cols < need_cols or height < need_rows:
                # §4e/§5 — a STATED refusal and ZERO panels, never a clipped one.
                msg = too_small_message(cols, height, need_cols, need_rows, worst)
                existing = self.query("#too-small")
                if existing:
                    existing.first(Static).update(msg)   # recomputed, not reused
                    return
                await frame.remove_children()
                await frame.mount(Static(msg, id="too-small"))
                return

            if self.query("#too-small") or not self.query(Panel):
                await frame.remove_children()
                await frame.mount(*[Horizontal(*tiles, classes="row")
                                    for tiles in rows if tiles])


# ---- starting it as a program ---------------------------------------------


def main() -> int:
    """Start the terminal. **029 — until now nothing did.**

    `MomentumApp` was defined here and never run, so `python -m live.tui.app`
    imported the module, executed these definitions, reached the end and exited
    **0**. No output, no traceback. 236 tests passed against it, because every
    one of them drives the app through Textual's `run_test()` pilot, which
    constructs the class directly and never needs a process entry point. **The
    suite was testing a library and the UAT was starting a program.**

    **The layout is loaded HERE and passed in**, rather than left to
    `MomentumApp.__init__`'s default. `SPEC.md` §4.4 — *no setting acquires a
    default* — and the launcher is the classic place one appears. Loading it
    explicitly also means a malformed `config/layout.yaml` fails **before**
    Textual takes the alternate screen buffer, so the traceback lands on a
    terminal that still works rather than one mid-teardown.

    **A record IS passed now, and 029's reason for not passing one is the reason
    it must be (034).** 029 said *there is no broker in this slice*; there is
    one from here on, and the only way HEALTH can say what happened to the
    connection is for the launcher to write it onto the record the panels are a
    pure function of.

    **The connection is attempted and its FAILURE IS A VALUE** — `connect()`
    never raises. `SPEC.md` §4.2, *surfaced, not refused*: with TWS closed, the
    app still launches, every panel renders, and HEALTH names the host, the port
    and why. **A launcher that exited because TWS was absent would be a refusal
    the user cannot read**, which is the same defect 029 fixed arriving through
    a different door.

    **Config is loaded BEFORE Textual takes the alternate screen buffer.** A
    malformed `config/ibkr.yaml` is a traceback on a terminal that still works,
    rather than one mid-teardown — the same reason the layout is loaded here.
    That is also why a bad config is allowed to raise while a bad *connection* is
    not: one is a file this repository controls and a person can fix in an
    editor; the other is the state of the world.

    **No arguments, no flags.** There is one command today. A `--headless`
    switch for the launch test would make this a second place where behaviour
    lives; the test selects Textual's headless driver through the environment
    instead.
    """
    layout = Layout.load()
    cfg = IbkrConfig.load()

    record = empty_record()
    broker = connect(cfg)
    if broker.ok:
        record.health.sources[broker.source] = broker.state
    else:
        record.health.unavailable_sources[broker.source] = broker.state

    try:
        MomentumApp(record=record, layout=layout, md=broker.md).run()
    finally:
        # The broker thread is a daemon, so this is not what keeps the process
        # from hanging — it is what releases the client id promptly. A client id
        # held by a dead-but-not-disconnected session is the collision the
        # config's note warns about, caused by us.
        broker.close()
    return 0


if __name__ == "__main__":
    # **Both this and `live/tui/__main__.py`, not one of them.** `-m live.tui`
    # is the form worth having, but `-m live.tui.app` is the command in
    # Christoph's shell history and he will type it again.
    raise SystemExit(main())

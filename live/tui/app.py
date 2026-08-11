"""The TUI frame — S009 §4b, §4d, §4e, §4g, §4h.

**Tiled, not switchable.** Watchlist, attached symbol and tape across the top;
sizing, risk and health along the bottom. Nothing hidden, nothing switched.
`Ctrl+Tab` rotates focus and **is the entire navigation surface**; `Ctrl+P` is
the palette for the long tail. No window management, no screen switching, no
drag-and-drop.

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
"""
from __future__ import annotations

import os
import sys
import unicodedata

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static

from .day_record import DayRecord, empty_record
from .grammar import Cell
from .layout import Layout

#: §4d — a fixed box width. The mockups were 69–71 chars against a 71-char
#: border: invisible in HTML, visibly broken in a console.
BOX_WIDTH = 71


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


def too_small_message(cols: int, rows: int, min_cols: int, min_rows: int) -> str:
    """§4e/§5 — a STATED refusal, never a silently clipped panel.

    It narrows to exactly ONE meaning: the pinned rows do not fit. Not "the
    layout is awkward", which is a different statement and would make the
    message useless for deciding anything.
    """
    return (f"window too small - the pinned rows do not fit "
            f"({cols}x{rows}, need {min_cols}x{min_rows})")


def box_top(title: str, provenance: str, width: int = BOX_WIDTH) -> str:
    """§4d — the RIGHT-HAND END of every top border carries provenance.

    Source, as-of time, sample window, or safety state. **A live panel with no
    update stamp is the `[ STALE ]` anti-state**, so `provenance` is not
    optional — callers pass a refusal string when they have nothing.
    """
    h, tl, tr = ("-", "+", "+") if ascii_safe() else ("─", "┌", "┐")
    left = f"{tl}{h} {title} "
    right = f" {provenance} {tr}"
    pad = width - display_width(left) - display_width(right)
    return left + (h * max(pad, 1)) + right


class Panel(Static):
    """One tile. Renders rows, and says so when there are more below (§4e).

    ***"Nothing more here"* and *"more below"* must not render identically.**
    A limit breach at row 19 of a 12-row viewport is indistinguishable from no
    breach — the sixth instance in this project of a correct warning nobody was
    instructed to read.
    """

    def __init__(self, title: str, provenance: str, rows: list[str],
                 pinned: list[str] | None = None, viewport: int = 8) -> None:
        self.title_text = title
        self.provenance = provenance
        self.rows = rows
        self.pinned = pinned or []
        self.viewport = viewport
        super().__init__(self._body())

    def _body(self) -> str:
        out = [box_top(self.title_text, self.provenance)]
        shown = self.rows[: self.viewport]
        out += shown
        hidden = len(self.rows) - len(shown)
        if hidden > 0:
            # Both halves of §4e: the count in the caption AND the edge marker.
            out.append(f"  {len(shown)} of {len(self.rows)} · +{hidden} more ↓")
        elif self.rows:
            out.append(f"  {len(self.rows)} of {len(self.rows)} · end")
        if self.pinned:
            # §4e — sticky band. Risk rows, limit rows, failed rules and active
            # refusals survive scrolling; without this the pinning rule is prose.
            out.append("  " + ("-" if ascii_safe() else "─") * (BOX_WIDTH - 4))
            out += [f"  {p}" for p in self.pinned]
        return "\n".join(out)


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
    p["attached"] = Panel(
        "ATTACHED", "not attached" if not at else f"since {at[0].since}",
        [f"  {a.symbol}  attached {a.since}" for a in at]
        or [f"  {Cell.absent('nothing attached').render()}"])

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
    p["health"] = Panel(
        "HEALTH", "updates · none yet",
        [f"  sources   {Cell.no_source('no feed connected').render()}"
         if not h.sources else f"  sources   {len(h.sources)} connected",
         f"  last seen {Cell.absent('nothing seen').render()}",
         f"  frames/ticks  {ratio}"],
        pinned=[f"regime    {Cell.not_built().render()}"
                if not record.regime_snapshot.ref
                else f"regime    {record.regime_snapshot.ref}"])
    return p


class MomentumApp(App):
    """The frame. Boots on an empty record and refuses, visibly, everywhere."""

    CSS = """
    Screen { layout: vertical; }
    .row { height: 1fr; }
    Panel { border: none; padding: 0 1; width: 1fr; }
    """
    BINDINGS = [("ctrl+tab", "focus_next", "Next panel")]

    #: §4e — `window too small` narrows to mean ONLY that the pinned rows do
    #: not fit. Not "the layout is awkward" — that is a different statement.
    MIN_COLS, MIN_ROWS = 60, 16

    def __init__(self, record: DayRecord | None = None, layout: Layout | None = None):
        self.record = record if record is not None else empty_record()
        self.layout_cfg = layout or Layout.load()
        super().__init__()

    def compose(self) -> ComposeResult:
        cols, rows = self.size.width or 0, self.size.height or 0
        if cols and rows and (cols < self.MIN_COLS or rows < self.MIN_ROWS):
            # §4e/§5 — a STATED refusal, never a silently clipped panel. And it
            # narrows to one meaning: the pinned rows do not fit.
            yield Static(
                too_small_message(cols, rows, self.MIN_COLS, self.MIN_ROWS),
                id="too-small")
            return
        panels = render_panels(self.record, self.layout_cfg)
        visible = [c.id for c in self.layout_cfg.visible_only]
        top = [panels[i] for i in ("watchlist", "attached", "tape") if i in visible]
        bottom = [panels[i] for i in ("sizing", "risk", "health") if i in visible]
        with Vertical():
            with Horizontal(classes="row"):
                for w in top:
                    yield w
            with Horizontal(classes="row"):
                for w in bottom:
                    yield w

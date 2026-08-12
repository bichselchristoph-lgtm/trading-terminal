"""The TUI frame — S009 §4b, §4d, §4e, §4g, §4h; S009a parts 1 and 3.

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

import os
import re
import sys
import unicodedata

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from .day_record import DayRecord, empty_record
from .grammar import Cell
from .layout import Layout

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
    """
    BINDINGS = [("ctrl+tab", "focus_next", "Next panel")]

    def __init__(self, record: DayRecord | None = None, layout: Layout | None = None):
        self.record = record if record is not None else empty_record()
        self.layout_cfg = layout or Layout.load()
        super().__init__()

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

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
import time
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
from core.indicators.context import (ADR_BASIS, ADR_DEFAULT_N, Bar,
                                     SessionBasis)

from ..attach.attach import (COOLDOWN_S, Contract, MarketData, Stage2Inputs,
                             attach, compute_context_and_rail)
# **034: the import that was missing one layer down.** `live/attach/ibkr.py` —
# the only module in this tree that touches a broker — was imported by nothing
# at all, not even a test, while 032 was fixing the same shape for `attach()`.
from ..attach.ibkr import IbkrConfig, connect
from ..attach.rvol_config import anchor_word, load_rvol_basis
from ..attach.streaming import StreamHandle
from .day_record import (Attached, AttachMetrics, DayRecord, RequestMetrics,
                         StreamMetrics, empty_record)
from .grammar import Cell
from .layout import Layout
from .numbers import (NO_BASIS, basis_label, format_value, needs_basis,
                      progress_bar)

#: **080 Part 3.** One threshold, every row. Unfitted — task 008b: median
#: 5.002s, max 14.477s, one 32-minute session of one symbol. Renders as
#: unfitted wherever provenance shows (this module has no provenance line
#: of its own to carry it on; the done-note states it).
STALE_THRESHOLD_S = 20.0

#: Roles whose bars arrive pre-split by session (a list of lists), so their
#: "received" count sums across sessions rather than counting the outer list.
_SESSION_ROLES = frozenset({"sessions", "sector_sessions"})


def _reason_str(exc: BaseException) -> str:
    """**080.** The same reason-extraction `attach.py._reason` already does
    — duplicated rather than imported, since it is three lines and importing
    a private function across a module boundary is a worse coupling than
    three duplicated lines (`attach.py`'s own module docstring: pacing is a
    display state, and the message is what a reader acts on)."""
    msg = str(exc).strip()
    return msg or type(exc).__name__


def _bar_count(role: str, bars) -> Optional[int]:
    """**080 Part 4.** `bars_received` for a landed role. `None` only when
    `bars` itself is `None` (the role returned nothing at all, which some
    `MarketData` implementations do for an absent sector); an empty
    sequence is a real, countable zero."""
    if bars is None:
        return None
    if role in _SESSION_ROLES:
        return sum(len(s) for s in bars)
    return len(bars)

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


#: **080.** Five rows: symbol (rendered separately, above these), `Last $`,
#: `ADR% used`, `RVOL`, `VWAP`. `RVOL_rel`/`RVOL_sector`/`cum vol` fold into
#: the single `RVOL` line (own reading first, sector-relative second, each
#: labelled with its basis — `avg`/`rel` are retired as labels); `VWAP`
#: renders its value alone, no signed distance (v1.5's own change — the old
#: `VWAP_ext` suffix compared `Last $` against itself once both were on the
#: same panel, B-127's third firing). `ADR%avail`, `ATR20`, `ext 10/20/50`
#: stay off this tuple as before — still computed, never displayed.
CONTEXT_ORDER = ("Last $", "ADR% used", "RVOL", "VWAP")

#: The level rail. **`VWAP` is deliberately absent** — `level_rail` carries it
#: and so does the context block, and rendering one value twice is how two rows
#: come to disagree after somebody fixes one of them.
RAIL_ORDER = ("PDH", "PDL", "PMH", "PML", "ORH5", "ORL5", "ORH15", "ORL15",
              "52wH", "52wL", "round")


def _cell_parts(m) -> Optional[tuple[str, str]]:
    """`(value text, detail text)` for a nominal `Measured`, or `None` when it
    must render as a refusal instead — the shared refusal check both
    `measured_cell` and 070's compound rows (`ADR% used`'s bar, the combined
    `RVOL rel` line, `VWAP`'s extension) go through, so a row that folds
    several `Measured` values into one line cannot skip the no-basis check by
    accident.
    """
    if not getattr(m, "ok", False):
        return None
    # **A value with no declared basis REFUSES.** 038's exit test, and it is a
    # refusal rather than a blank label on purpose: an unlabelled number on this
    # panel is the whole defect 038 exists to close. ADR and ATR sit four rows
    # apart, are both labelled volatility, and are computed on different sessions
    # deliberately — a reader who cannot see that compares them.
    if needs_basis(m) and basis_label(m) is None:
        return None
    text = Cell.value(format_value(m)).render()
    # **Basis last, after the sample.** The sample says what it was computed
    # OVER — `20 sessions, excl. today` — and the basis says WHICH BARS those
    # sessions were, which is the qualifier on everything before it.
    detail = " · ".join(x for x in (m.sample, basis_label(m)) if x)
    return text, detail


def measured_cell(m) -> str:
    """A `Measured` through the refusal grammar.

    **`sample` rides with the number** — S010 requires it on every rendered
    value, and a bare `2.00` is a value with nothing behind it, which is the
    thing tenet 2 and this whole module exist to prevent. An absent `Measured`
    already names its own reason, so it goes through `Cell.absent` and renders
    `— (need 21 daily bars, have 5)` rather than a blank.
    """
    parts = _cell_parts(m)
    if parts is None:
        if not getattr(m, "ok", False):
            return Cell.absent(getattr(m, "unavailable", "") or "absent").render()
        return Cell.absent(NO_BASIS).render()
    text, detail = parts
    return f"{text}  · {detail}" if detail else text


def _adr_used_cell(m) -> str:
    """071. `ATTACHED` mockup v1.2 §1: `16.7% ▓▓▓░░░░░░░░░░ of $10.66 ADR20
    RTH` — replaces 070's `text  bar  · sample · basis_label` join (verbose
    enough on its own to overflow the 62-column tile without truncating,
    which the mockup's own caption calls out as the point of this reduction).

    **Bespoke, not `_cell_parts`'s generic `detail`.** `ADR20`/`RTH` is built
    directly from `ADR_DEFAULT_N` and `m.basis.use_rth` — not routed through
    `basis_label()`'s closed vocabulary of clock windows, because it isn't
    one; it is this one row's own compact code. `m.sample` (still just the
    dollar figure — see `adr_used()`'s docstring) supplies the `$10.66`.

    **`m.value` is not clamped**; only `progress_bar`'s OWN fill is, per
    `adr_used`'s docstring.

    **Reported, not silently dropped:** 038 Part 6 row 1 added "from today's
    open" specifically so the row answered what it anchors to. This compact
    form does not say it — the mockup was drawn without it, from a live
    screenshot, and the mockup wins on layout. The anchor is still on
    `Measured.sample`/`.basis` for anyone reading the object directly; it is
    just not spelled out on screen any more.
    """
    parts = _cell_parts(m)
    if parts is None:
        return measured_cell(m)
    text, _detail = parts
    bar = progress_bar(m.value)
    window = "RTH" if m.basis is not None and m.basis.use_rth else "ETH"
    return f"{text} {bar} of {m.sample} ADR{ADR_DEFAULT_N} {window}"


#: **080.** Every pending row says this, verbatim, and nothing else does —
#: the Refusal exit test pins the literal token so `pending` and a stale
#: value can never render alike.
PENDING = "pending"


def _age_now(last_update_at: Optional[float]) -> Optional[float]:
    """Seconds since a stream last updated, or `None` if it never has.
    `time.monotonic()`, matching `_PacingGuard`'s own clock — never wall
    time, which a DST change or a session boundary can jump."""
    if last_update_at is None:
        return None
    return time.monotonic() - last_update_at


def _stale_suffix(age: Optional[float]) -> str:
    """**080 Part 3.** The single place `stale Ns` gets written. Empty for
    a fresh or not-yet-aged reading — this IS the amber exception, rendered
    as text rather than colour (this codebase has no colour-rendering layer
    anywhere; every other state distinction here is already typographic —
    `~`, `?`, `[ ]`, `—` — and this follows the same convention rather than
    inventing a first one). The Colour exit test asserts this string never
    appears anywhere except where it belongs."""
    if age is None or age < STALE_THRESHOLD_S:
        return ""
    return f" stale {int(age)}s"


def _rvol_row(a: "Attached") -> str:
    """**080.** `0.86x own · 1.4x vs XLC` — own-history reading first
    (`RVOL`, read first in `compute_context_and_rail` too), sector-relative
    second (`RVOL_rel`), each labelled with its basis. `avg`/`rel`/`cum` are
    retired as labels — `cum vol` stays computed, off this row entirely
    (082's own instruction: the check is that the TEXT is absent, not that
    the field is absent, the opposite of B-028's `ADR$` treatment).

    **One reading refusing never blanks the other — B-117**, and one
    reading PENDING never blanks the other either, which is the same
    property extended to the new state 080 adds: `own`/`rel` are read from
    `a.context` independently, so `0.86x own · pending` (the 20-session
    sector pull still in flight while the symbol's own curve already
    landed) is reachable and correctly does not blank `own`.

    **Amber is per reading**, because the two readings track two
    independent stream ages — `own` the symbol stream, `rel` the sector
    stream (080 Part 3, the task's own words: "two streams, two independent
    ages").

    **083: the label carries the anchor** — `RVOL rth`/`RVOL eth`, derived
    from `a.rvol_anchor` (never a literal), which renders even while the
    row is pending because the anchor is a fact about the row, known at
    attach, not about a value that has landed yet.
    """
    label = f"RVOL {a.rvol_anchor}" if a.rvol_anchor else "RVOL"
    own = a.context.get("RVOL")
    rel = a.context.get("RVOL_rel")
    if own is None and rel is None:
        return f"    {label:<12} {PENDING}"

    symbol_age = _age_now(a.metrics.streams.get("symbol", StreamMetrics()).last_update_at)
    sector_age = _age_now(a.metrics.streams.get("sector", StreamMetrics()).last_update_at)

    if own is None:
        own_text = PENDING
    else:
        own_parts = _cell_parts(own)
        own_text = (f"{own_parts[0]} own{_stale_suffix(symbol_age)}"
                   if own_parts is not None else measured_cell(own))

    if rel is None:
        rel_text = PENDING
    else:
        rel_parts = _cell_parts(rel)
        if rel_parts is not None:
            rel_label = f"vs {a.sector_etf}" if a.sector_etf else "vs sector"
            rel_text = f"{rel_parts[0]} {rel_label}{_stale_suffix(sector_age)}"
        else:
            rel_text = measured_cell(rel)

    return f"    {label:<12} {own_text}  · {rel_text}"


def _vwap_row(vwap) -> str:
    """**080/v1.5.** The value and nothing else — `VWAP $714.25`. The
    signed-distance suffix (`VWAP_ext`, `· +$1.28`) this row carried since
    070 is gone: once `Last $` joined this panel (080), the two read the
    same underlying price and the distance became self-contradictory
    whenever they drifted (v1.5 §2, B-127's third firing) — a reader with
    both numbers on screen can already do the subtraction; the row states
    the level. `vwap_from_bars` itself is untouched."""
    if vwap is None:
        return f"    {'VWAP':<12} {PENDING}"
    parts = _cell_parts(vwap)
    if parts is None:
        return f"    {'VWAP':<12} {measured_cell(vwap)}"
    text, _detail = parts
    return f"    {'VWAP':<12} {text}"


def _adr_row(m) -> str:
    if m is None:
        return f"    {'ADR% used':<12} {PENDING}"
    return f"    {'ADR% used':<12} {_adr_used_cell(m)}"


def _last_price_row(m) -> str:
    """**080.** `Last $` — the last trade, off the price stream. **Never
    `pending`** (080 Part 2, verbatim): the row's nature is a live tick, not
    a queued historical fetch, so its brief pre-first-tick state uses the
    grammar's existing `not_yet`/`warming` wording instead of the literal
    `pending` token every other row in this panel uses — distinct on
    purpose, since it is a structurally different wait (a stream opening,
    never bounded at 60s the way a historical request is)."""
    if m is None:
        return f"    {'Last $':<12} {Cell.not_yet().render()}"
    parts = _cell_parts(m)
    if parts is None:
        return f"    {'Last $':<12} {measured_cell(m)}"
    text, _detail = parts
    return f"    {'Last $':<12} {text}"


def context_rows(a: Attached) -> list[str]:
    """The context block for one attached symbol: `Last $`, `ADR% used`,
    `RVOL`, `VWAP`. **080: rows land independently, each pending until it
    does** — there is no longer a screen-level partial-count line (058/071's
    `a.partial`); five rows and the header are all this panel renders, per
    the task's own §4 constraint, and a row's own state (pending / value /
    `— (reason)`) already says everything the old summary line said.

    **Indented one level under its symbol**, because the panel holds a list of
    attachments and a flat block would read as belonging to whichever symbol the
    eye landed on last.

    **`from`/`slot`/`tape` and the level rail are no longer this function's
    concern.** 071 §4 moves each to a different screen (SOURCES/HEALTH, a
    future slot indicator, TAPE, the LEVELS rail) without deleting the data
    they were reading — `Attached` still carries `source`/`as_of`/`lag`/
    `slot_state`/`tape`/`rail`, populated exactly as before; this function
    just stops reading them.
    """
    rows: list[str] = []
    for name in CONTEXT_ORDER:
        if name == "Last $":
            rows.append(_last_price_row(a.context.get("Last $")))
        elif name == "ADR% used":
            rows.append(_adr_row(a.context.get("ADR% used")))
        elif name == "RVOL":
            rows.append(_rvol_row(a))
        elif name == "VWAP":
            rows.append(_vwap_row(a.context.get("VWAP")))
    return rows


def header_freshness(a: Attached) -> str:
    """**080 Part 3.** The header's age suffix — `4s`, `stale 34s`, or `` (a
    bare header, the broken state, B-134: the freshness computation is not
    running at all). **The older of the two stream ages** — never more
    optimistic than the worst reading on the panel. A stream absent from
    `a.metrics.streams` (no sector mapping) never contributes; one present
    but never yet updated (`last_update_at is None`) is filtered out rather
    than forcing bare, so a healthy symbol stream still renders its own age
    while the sector stream is still opening.
    """
    ages = [age for age in
            (_age_now(sm.last_update_at) for sm in a.metrics.streams.values())
            if age is not None]
    if not ages:
        return ""
    oldest = max(ages)
    return f"stale {int(oldest)}s" if oldest >= STALE_THRESHOLD_S else f"{int(oldest)}s"


def attach_metrics_rows(record: DayRecord) -> list[str]:
    """**080 Part 4.** What Part 4 asks for, rendered where it asks for it —
    never on ATTACHED. Per-stream (symbol/sector **separately, never
    pooled**) update counts and ages; per-request wall time and bar counts;
    per-stage keypress-to-paint. Empty when nothing is attached.

    **States the trap rather than hiding it** (Part 4's own instruction): a
    degraded supplier and a quiet market both read as a long gap here —
    this renders the NUMBER, not a verdict about what produced it.
    """
    if not record.attached:
        return []
    m = record.attached[0].metrics
    rows: list[str] = []
    for name, sm in sorted(m.streams.items()):
        age = _age_now(sm.last_update_at)
        age_text = f"{int(age)}s ago" if age is not None else "no update yet"
        err = f" - {sm.error}" if sm.error else ""
        rows.append(f"  stream {name:<7} {sm.update_count} updates · {age_text}{err}")
    for role, rm in sorted(m.requests.items()):
        wall = f"{rm.wall_s:.1f}s" if rm.wall_s is not None else "—"
        bars = f"{rm.bars_received} bars" if rm.bars_received is not None else "— bars"
        err = f" - {rm.error}" if rm.error else ""
        rows.append(f"  role {role:<15} {wall} · {bars}{err}")
    if m.stage1_keypress_to_paint_s is not None:
        rows.append(f"  stage1 keypress-to-paint  {m.stage1_keypress_to_paint_s:.2f}s")
    if m.stage2_first_row_s is not None:
        rows.append(f"  stage2 first row          {m.stage2_first_row_s:.2f}s")
    if m.stage2_last_row_s is not None:
        rows.append(f"  stage2 last row           {m.stage2_last_row_s:.2f}s")
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
    # **058 Part 3 — the atomic swap, corrected by 072.** `record.attached`
    # is NOT cleared while a gather is in flight any more (`_begin_attach`) —
    # it has to survive a FAILED attach intact (`SPEC.md` §4.2). So the
    # screen-level blank is enforced HERE instead: `at` renders only when
    # neither an attach nor a cooldown-queue is in flight. One screen-level
    # state, not a per-cell pending state — `BUILD-PLAN` slice 010 §7 wins
    # over §3's retired `fetching dailies…`.
    if not record.attaching and not record.attach_queued:
        for a in at:
            attach_rows.append(f"  {a.symbol}  attached {a.since}")
            attach_rows += context_rows(a)
    if record.attach_queued:
        # **070 §6.** Never a silent drop: the whole gather refused before
        # step 3 ran (`attach.py`'s cooldown branch), and the panel says so
        # in plain text — not a `Cell` badge, matching `slot_state`'s own
        # `queued - Ns` string, which this supersedes for the SAME cooldown
        # clock at the moment it blocks the entire attach rather than just
        # the tape.
        symbol, remaining = record.attach_queued.split(" ", 1)
        attach_rows.append(f"  {symbol} queued · {remaining} "
                           f"({COOLDOWN_S}s same-contract cooldown)")
    elif record.attaching:
        # **080.** Stage 1 alone gates this window now — contract
        # resolution, measured 0.23-0.25s — not the whole gather 071's
        # "one paint" described. Rows landing independently is stage 2's
        # story, told entirely inside `context_rows` once `at` is non-empty;
        # this placeholder only covers the brief span before even the
        # symbol row exists.
        attach_rows.append("  (resolving)")
    if record.attach_refusal:
        attach_rows.append(f"  {Cell.absent(record.attach_refusal).render()}")
    if record.attach_queued:
        provenance = f"queued · {record.attach_queued.split(' ', 1)[1]}"
    elif record.attaching:
        # **071 §5.** No brackets — mockup v1.2 §3's caption is plain
        # `ATTACHING QQQ`, not the `[ ATTACHING QQQ ]` badge `Cell.attaching`
        # renders. The symbol row inside the panel carries the attach time
        # with seconds; this caption carries the in-flight state.
        provenance = f"ATTACHING {record.attaching}"
    elif not at:
        provenance = "not attached"
    elif record.attach_refusal:
        # **072 Defect B.** A symbol remains attached (`at` is non-empty)
        # and the MOST RECENT attach attempt refused — the caption says so
        # rather than staying bare, because bare is 071's signal for
        # "nothing to report" and a refused re-attach is exactly something
        # to report. `Cell.absent(record.attach_refusal)` already renders
        # below, naming which symbol and why; this caption is what a reader
        # sees before reading that far.
        provenance = "attach refused"
    else:
        # **080 Part 3, reversing 071 §3.** The header now carries the
        # freshness age, always — "the age renders always... a bare header
        # means the freshness age is not being computed" (B-134). Bare is
        # no longer 071's "nothing to report" signal; it is the BROKEN
        # state. `record.attached` holds at most one entry (SPEC.md
        # §12.11), so there is exactly one symbol's freshness to report.
        provenance = header_freshness(at[0]) if at else ""
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
        source_rows + last_seen_rows + [f"  frames/ticks  {ratio}"]
        + attach_metrics_rows(record),
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
        #: **080.** Every open stream the CURRENT attach owns — cancelled and
        #: replaced wholesale on the next `_begin_attach` (task's own words:
        #: "attaching a different symbol cancels every data stream of the
        #: current one").
        self._streams: list[StreamHandle] = []
        #: Bumped on every `_begin_attach`. A callback carries the
        #: generation it was dispatched under; one that arrives after a
        #: newer attach has begun is inert, even if `cancel()` could not
        #: stop a request already on the wire.
        self._attach_generation = 0
        #: Stage 2's accumulated inputs for the CURRENT attach — reset to a
        #: fresh instance on every `_begin_attach`.
        self._stage2_inputs = Stage2Inputs()
        self._stage1_started_at: Optional[float] = None
        self._stage2_started_at: Optional[float] = None
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
            self.record.attach_queued = ""
            self.record.attached = [a for a in self.record.attached
                                    if a.symbol != symbol]
            self.record.attach_refusal = (
                f"{symbol}: no market data - the app connects to "
                "no broker in this slice")
            await self._rerender()
            return
        generation = self._begin_attach(symbol)
        await self._rerender()
        self.run_worker(functools.partial(self._attach_worker, symbol, generation),
                        thread=True, exclusive=False, group="attach",
                        name=f"attach-{symbol}")

    def _begin_attach(self, symbol: str) -> None:
        """**058 Part 3, the atomic swap's first step.** Every value
        dependent on the outgoing symbol is dropped IMMEDIATELY FROM THE
        SCREEN — not left on screen, not greyed. `ATTACHED` §6b.5 rules that
        a DETACHED symbol renders `STALE`; this is a RE-ATTACH of the same
        symbol (or a fresh one), and a value from the previous attach
        sitting under the new header while the new one is still in flight
        is the §7 archetype: a well-formed value answering a different
        question.

        **072: does NOT clear `record.attached` any more — `render_panels`
        does, by not rendering `at` at all while `record.attaching` is set
        (see there).** The two used to be the same thing (clearing the
        record WAS how the screen went blank), which is exactly what broke:
        clearing unconditionally here (072's first attempt at this fix)
        meant a FAILED second attach permanently lost the first symbol —
        `_finish_attach`'s failure branches never re-add it, and nothing
        else does either. `SPEC.md` §4.2 is explicit that a failed attach
        must not blank a symbol that is working, so the record has to
        survive a failed attempt intact; only the SCREEN may blank
        immediately, and only the render layer can tell "in flight" from
        "landed" without also needing to distinguish "the new attach
        succeeded" from "it is about to fail," which is not yet knowable
        here.

        **`record.attached` still holds at most one entry** (`SPEC.md`
        §12.11 — several symbols at once is deferred) — enforced in
        `_finish_stage1`'s success branch, which clears fully before
        appending, rather than here.

        **080: also cancels every stream the OUTGOING symbol opened, and
        bumps the generation.** Returns the new generation so the caller can
        tag the worker it is about to dispatch with it — a callback tagged
        with a stale generation is inert even when `cancel()` could not stop
        a request already on the wire.
        """
        self.record.attach_refusal = ""
        self.record.attach_queued = ""
        self.record.attaching = symbol
        for handle in self._streams:
            handle.cancel()
        self._streams = []
        self._attach_generation += 1
        self._stage2_inputs = Stage2Inputs()
        # **083.** Loaded fresh per attach — `config/rvol.yaml` is small and
        # this makes an edited anchor take effect on the next attach without
        # a restart. A load failure falls back to `Stage2Inputs`'s own
        # default (RTH) rather than refusing the attach outright — a
        # config file this session just wrote and validates on every read
        # failing mid-session is not a scenario worth blanking the panel
        # over; stated here as a deliberate, narrow exception to "fail
        # loud," not an oversight.
        try:
            self._stage2_inputs.rvol_basis = load_rvol_basis()
        except Exception:                                # noqa: BLE001
            pass
        self._stage1_started_at = time.monotonic()
        self._stage2_started_at = None
        return self._attach_generation

    def _attach_worker(self, symbol: str, generation: int) -> None:
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
            self.call_from_thread(self._finish_stage1, symbol, generation, None,
                                  f"{symbol}: attach failed "
                                  f"({type(exc).__name__}: {exc})")
            return
        self.call_from_thread(self._finish_stage1, symbol, generation, result, None)

    async def _finish_stage1(self, symbol: str, generation: int, result,
                             worker_refusal: Optional[str]) -> None:
        """**080: stage 1's landing.** Runs on the main thread (via
        `call_from_thread`), so this and `_begin_attach` are the only two
        places that mutate `record.attached`/`record.attaching`.

        **Paints symbol + order-ready state alone — no context, no rail.**
        Those are stage 2's, and stage 2 is dispatched from HERE, the
        instant stage 1 lands successfully — not awaited, not blocking this
        paint. A stale generation (a newer attach already began while this
        one was in flight) is a no-op; `_begin_attach` already cancelled
        whatever streams this one might have opened.
        """
        if generation != self._attach_generation:
            return
        self.record.attaching = ""
        if worker_refusal is not None:
            self.record.attach_refusal = worker_refusal
            self.record.attach_queued = ""
        elif result.queued:
            # **070 §6.** Checked before `not result.attached` — a queued
            # re-attach never set `refusal`, so falling through to that
            # branch would render `SYMBOL: ` with nothing after the colon.
            self.record.attach_queued = f"{result.symbol} {result.queued}"
            self.record.attach_refusal = ""
        elif not result.attached:
            # `AttachResult` already carries the failure — render it, do not
            # re-word it. Ambiguity in particular carries its candidate count,
            # and a shorter message would drop the number that makes it useful.
            self.record.attach_refusal = f"{result.symbol}: {result.refusal}"
            self.record.attach_queued = ""
        else:
            # An attach that failed at steps 2-4 is still an attach, so a
            # stale refusal from a previous attempt must not survive one.
            # **072 Defect A's fix, unchanged**: a SUCCESSFUL attach clears
            # `record.attached` unconditionally rather than filtering, and
            # only a successful one — a failed attach must leave whatever
            # was there untouched (§4.2).
            self.record.attached = []
            a = Attached(symbol=result.symbol,
                        # **071 §3.** Seconds, not minutes.
                        since=datetime.now(EASTERN).strftime("%H:%M:%S"),
                        sector_etf=(result.contract.sector_etf or ""
                                   if result.contract else ""),
                        # **083.** Known at attach, not at landing — set from
                        # the SAME `Stage2Inputs.rvol_basis` instance stage
                        # 2's own dispatch will read, so the rendered word
                        # can never name a different anchor than the one the
                        # request actually used.
                        rvol_anchor=anchor_word(self._stage2_inputs.rvol_basis),
                        source=self.source_name,
                        tape=result.tape, slot_state=result.slot_state)
            if self._stage1_started_at is not None:
                a.metrics.stage1_keypress_to_paint_s = (
                    time.monotonic() - self._stage1_started_at)
            self.record.attached.append(a)
            self.record.attach_refusal = ""
            self.record.attach_queued = ""
            await self._rerender()
            self._dispatch_stage2(result.contract, generation)
            return
        await self._rerender()

    # ---- 080, stage 2: independent landing --------------------------------

    def _dispatch_stage2(self, contract: Contract, generation: int) -> None:
        """**080 Part 1/Part 0 item 3.** Dispatched the instant stage 1's
        contract resolves — built and tested as ROUGHLY the same cost as
        sequencing it after stage 1, since every call below is already an
        independent, non-blocking `run_worker(thread=True)` dispatch onto
        the SAME shared broker connection; adding a second wave later would
        be the more expensive shape to build, not this one (see the
        done-note for the full reasoning).

        Two `keepUpToDate` streams (symbol, sector — only if a mapping
        exists) and up to three one-shot historical requests, each its own
        worker, each landing and repainting independently.
        """
        self._stage2_inputs.has_sector = bool(contract.sector_etf)
        self._stage2_started_at = time.monotonic()

        self.run_worker(
            functools.partial(self._stream_worker, contract, generation,
                              "symbol", contract),
            thread=True, exclusive=False, group="attach",
            name=f"stream-symbol-{contract.symbol}")

        if contract.sector_etf:
            sector_c = Contract(symbol=contract.sector_etf, con_id=0, exchange="SMART")
            self.run_worker(
                functools.partial(self._stream_worker, contract, generation,
                                  "sector", sector_c),
                thread=True, exclusive=False, group="attach",
                name=f"stream-sector-{contract.symbol}")

        # **083.** Captured once, on the main thread, from the SAME
        # `Stage2Inputs.rvol_basis` the numerator-filtering code reads —
        # passed to the worker rather than read from `self._stage2_inputs`
        # again on a different thread, so there is exactly one read of the
        # config per attach, not one per role.
        rvol_basis = self._stage2_inputs.rvol_basis
        self.run_worker(
            functools.partial(self._role_worker, contract, generation, "rth_dailies"),
            thread=True, exclusive=False, group="attach",
            name=f"role-rth-dailies-{contract.symbol}")
        self.run_worker(
            functools.partial(self._role_worker, contract, generation, "sessions",
                              rvol_basis),
            thread=True, exclusive=False, group="attach",
            name=f"role-sessions-{contract.symbol}")
        if contract.sector_etf:
            self.run_worker(
                functools.partial(self._role_worker, contract, generation,
                                  "sector_sessions", rvol_basis),
                thread=True, exclusive=False, group="attach",
                name=f"role-sector-sessions-{contract.symbol}")

    def _stream_worker(self, owner: Contract, generation: int, which: str,
                       stream_contract: Contract) -> None:
        """Opens ONE `keepUpToDate` stream and blocks only long enough to
        register it — `on_update` then fires for the rest of the stream's
        life, each firing marshalled back via `call_from_thread` exactly as
        `_attach_worker`'s single result used to be."""
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        def on_update(bars) -> None:
            self.call_from_thread(self._apply_stream_update, generation, which, bars)

        try:
            handle = self.md.open_price_stream(stream_contract, on_update)
        except Exception as exc:                        # noqa: BLE001
            self.call_from_thread(self._apply_stream_error, generation, which,
                                  _reason_str(exc))
            return
        self.call_from_thread(self._register_stream, generation, handle)

    def _register_stream(self, generation: int, handle: StreamHandle) -> None:
        if generation != self._attach_generation:
            handle.cancel()
            return
        self._streams.append(handle)

    async def _apply_stream_update(self, generation: int, which: str, bars) -> None:
        if generation != self._attach_generation or not self.record.attached:
            return
        a = self.record.attached[0]
        now = time.monotonic()
        sm = a.metrics.streams.setdefault(which, StreamMetrics(label=which))
        if sm.last_update_at is not None:
            sm.gaps_s.append(now - sm.last_update_at)
            if len(sm.gaps_s) > 200:
                sm.gaps_s.pop(0)
        sm.update_count += 1
        sm.last_update_at = now
        if which == "symbol":
            self._stage2_inputs.today = bars
        else:
            self._stage2_inputs.sector_today = bars
        self._recompute_and_merge(a)
        await self._rerender()

    async def _apply_stream_error(self, generation: int, which: str, reason: str) -> None:
        if generation != self._attach_generation or not self.record.attached:
            return
        a = self.record.attached[0]
        a.metrics.streams.setdefault(which, StreamMetrics(label=which)).error = reason
        if which == "symbol":
            self._stage2_inputs.today_failed = reason
        else:
            self._stage2_inputs.sector_today_failed = reason
        self._recompute_and_merge(a)
        await self._rerender()

    def _role_worker(self, contract: Contract, generation: int, role: str,
                     rvol_basis: Optional[SessionBasis] = None) -> None:
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        started = time.monotonic()
        try:
            if role == "rth_dailies":
                bars = self.md.daily_bars(contract, ADR_BASIS)
            elif role == "sessions":
                bars = self.md.intraday_sessions(contract, rvol_basis)
            elif role == "sector_sessions":
                bars = self.md.sector_sessions(contract, rvol_basis)
            else:                                        # pragma: no cover
                raise ValueError(f"unknown stage-2 role {role!r}")
        except Exception as exc:                        # noqa: BLE001
            self.call_from_thread(self._apply_role_error, generation, role,
                                  time.monotonic() - started, _reason_str(exc))
            return
        self.call_from_thread(self._apply_role_landed, generation, role,
                              time.monotonic() - started, bars)

    async def _apply_role_landed(self, generation: int, role: str, wall_s: float,
                                 bars) -> None:
        if generation != self._attach_generation or not self.record.attached:
            return
        a = self.record.attached[0]
        a.metrics.requests[role] = RequestMetrics(
            role=role, wall_s=wall_s, bars_received=_bar_count(role, bars))
        if role == "rth_dailies":
            self._stage2_inputs.rth_dailies = bars
        elif role == "sessions":
            self._stage2_inputs.sessions = bars
        elif role == "sector_sessions":
            self._stage2_inputs.sector_sessions = bars
        self._recompute_and_merge(a)
        self._note_row_landing()
        await self._rerender()

    async def _apply_role_error(self, generation: int, role: str, wall_s: float,
                                reason: str) -> None:
        if generation != self._attach_generation or not self.record.attached:
            return
        a = self.record.attached[0]
        a.metrics.requests[role] = RequestMetrics(role=role, wall_s=wall_s, error=reason)
        if role == "rth_dailies":
            self._stage2_inputs.rth_dailies_failed = reason
        elif role == "sessions":
            self._stage2_inputs.sessions_failed = reason
        elif role == "sector_sessions":
            self._stage2_inputs.sector_sessions_failed = reason
        self._recompute_and_merge(a)
        self._note_row_landing()
        await self._rerender()

    def _recompute_and_merge(self, a: Attached) -> None:
        """**080.** The one call site for `compute_context_and_rail` —
        merges NEW rows in, never removes one that already landed (`inp`'s
        fields only ever go from absent to present/failed, never back, so a
        recompute can only add or replace, never blank)."""
        ctx, rail = compute_context_and_rail(self._stage2_inputs)
        a.context.update(ctx)
        if rail:
            a.rail.update(rail)
        vwap = ctx.get("VWAP") or a.context.get("VWAP")
        if vwap is not None:
            a.as_of, a.lag = self._stamp({"VWAP": vwap})

    def _note_row_landing(self) -> None:
        if self._stage2_started_at is None or not self.record.attached:
            return
        a = self.record.attached[0]
        elapsed = time.monotonic() - self._stage2_started_at
        if a.metrics.stage2_first_row_s is None:
            a.metrics.stage2_first_row_s = elapsed
        a.metrics.stage2_last_row_s = elapsed

    def _stamp(self, context: dict) -> tuple[str, str]:
        """As-of and lag for the block, **derived from the DATA, never the clock
        alone.** The as-of is the last session bar's own timestamp; the lag is
        now minus that. A stamp taken at render time would say when the screen
        was painted, which is exactly the reading this project is named for.

        Both are empty when there is no bar to read one from — `context_rows`
        then renders the stamp without them rather than inventing one.

        **080: takes a `context` dict, not an `AttachResult`** — there is no
        longer one gather producing both at once; called from
        `_recompute_and_merge` whenever `VWAP` is present.
        """
        vwap = context.get("VWAP")
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
        """Rebuild the tiles from the record.

        **080: the empty-then-remount dance moved INSIDE `_apply_fit`'s own
        lock.** Emptying the frame here, THEN calling `_apply_fit()`
        separately, left a window between the two where a second concurrent
        `_rerender()` (080 calls this from many independent callback sites
        now — every stream tick, every row landing, not just one atomic
        swap) could remove the SAME already-empty frame and mount before
        this call's own `_apply_fit()` ran, which then saw panels already
        present and mounted nothing — an empty frame reaching the screen.
        `force=True` makes the whole remove-then-mount decision one atomic
        step under `_fit_lock`, the same guarantee `060`/B-001 already
        established for concurrent resize-vs-attach; this is that guarantee
        extended to concurrent attach-vs-attach.
        """
        await self._apply_fit(force=True)

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

    async def _apply_fit(self, *, force: bool = False) -> None:
        """Switch between the refusal and the panels, **in both directions.**

        A one-way transition would be worse than what it replaces: a terminal
        that refuses once and never comes back is a terminal you restart, and
        restarting to recover from a resize teaches you not to resize.

        **The message is RECOMPUTED on every call, never reused.** A refusal
        naming the launch size while the window is now a different size is a
        well-formed value answering a different question — the defect this
        project is named for, rendered in the widget whose job is to prevent it.

        **`force=True`** (080): `_rerender()`'s caller — remove and remount
        unconditionally, as one atomic step under the lock below, rather
        than trusting a prior `not self.query(Panel)` check that a second
        concurrent caller could have already invalidated.
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
                if existing and not force:
                    existing.first(Static).update(msg)   # recomputed, not reused
                    return
                await frame.remove_children()
                await frame.mount(Static(msg, id="too-small"))
                return

            if force or self.query("#too-small") or not self.query(Panel):
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

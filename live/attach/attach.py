"""The attach sequence — S010 part 1, `SPEC.md` §6b.1a-seq.

**080 splits this into two stages.** `attach()` below is now STAGE 1 alone —
resolve, cooldown, slot, tape, playbook. **Stage 2 — the historical requests
that feed `ADR% used`, `RVOL` and `VWAP` — is not a function call any more.**
It is `Stage2Inputs`/`compute_context_and_rail` (bottom of this file): a pure
recompute driven by whichever inputs have landed so far, called by `app.py`
every time one more of them arrives. **That is the mechanism "rows land
independently" runs on** — there is no longer a single gathered call for the
caller to wait on.

    | # | step                          | blocking | on failure                    |
    |---|-------------------------------|----------|-------------------------------|
    | 1 | resolve the contract          | YES      | ambiguous -> render, ask      |
    | 2 | check the tick slot           | no       | render NOW, name what to drop |
    | 3 | open the tick-by-tick stream  | no       | attach SUCCEEDS, tape absent  |
    | 4 | bind the playbook             | no       | `no trigger level declared`   |

**Stage 1 alone is enough to submit an order — this is the whole point of
080.** Nothing in stage 1 waits on a historical request; `app.py` dispatches
the price stream and the three stage-2 roles the moment step 1 resolves, and
none of stage 2 gates this function's return.

**Step 2 precedes step 3 deliberately.** With no slot you should learn that in
the first frame.

----

**`MarketData` is a Protocol, and that is what makes this slice testable.**
Every fixture in `live/tests/test_attach.py` is a fake implementing it, so the
entire surface — including all four refusals — is exercised with no TWS
connection at all. That mattered on the day it was built: the `019` capture held
the only client and could not be risked.

**Nothing here writes to disk.** `test_no_disk_write_on_the_attach_path` asserts
it rather than trusting this sentence — S010 part 2 requires a test, because
*if this slice needs a cache, the no-local-database decision was wrong.*
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol, Sequence

from core.indicators.context import (ADR_BASIS, Bar, INTRADAY_BASIS, Measured,
                                     PRIOR_DAY_BASIS, SMA_BASIS, SessionBasis,
                                     Unit, adr_dollar, adr_pct, adr_used,
                                     cumulative_volume, extension_in_adr,
                                     level_rail, rvol_at, rvol_curve,
                                     rvol_rel, sma, vwap_from_bars)
from .streaming import StreamHandle

#: The three origins, recorded from day one **even though only `typed` exists.**
#: `scanner` and `watchlist` arrive in later slices; recording the field now
#: means the day record does not change shape when they do, and a shape change
#: to a record already carrying evidence is the expensive kind.
ORIGINS = ("typed", "scanner", "watchlist")

#: `reqTickByTickData` is what the five concurrent slots limit. Historical bar
#: requests consume NONE, and `reqMktData` lines are a third budget (~100).
#: **Do not conflate the three** — the whole of step 4's independence from
#: step 3 rests on the distinction.
TICK_SLOTS = 5

#: IBKR's same-contract historical cooldown.
COOLDOWN_S = 15


@dataclass(frozen=True)
class Contract:
    symbol: str
    con_id: int
    exchange: str
    currency: str = "USD"
    primary: str = ""
    sector_etf: Optional[str] = None


class MarketData(Protocol):
    """Everything the attach path is allowed to ask the outside world for."""

    def resolve(self, symbol: str) -> Sequence[Contract]: ...
    def tick_slots_in_use(self) -> int: ...
    def cooldown_remaining_s(self, symbol: str) -> int: ...
    #: **080.** No longer called by `attach()` — stage 2's roles are now
    #: fetched independently (`app.py` calls `daily_bars`/`intraday_sessions`
    #: /`sector_sessions` directly, each from its own worker), so there is no
    #: single gathered call left for this to warm ahead of. Kept on the
    #: Protocol and on `IBKRMarketData` unchanged: nothing in this task asks
    #: for its removal, and a future direct caller (a fixture, a diagnostic)
    #: still has a working no-op/real implementation to call.
    def warm(self, c: Contract) -> None: ...
    def daily_bars(self, c: Contract, basis: SessionBasis) -> Sequence[Bar]: ...
    def intraday_sessions(self, c: Contract) -> Sequence[Sequence[Bar]]: ...
    def today_minutes(self, c: Contract) -> Sequence[Bar]: ...
    def sector_today_minutes(self, c: Contract) -> Optional[Sequence[Bar]]: ...
    def sector_sessions(self, c: Contract) -> Optional[Sequence[Sequence[Bar]]]: ...
    def open_tick_stream(self, c: Contract) -> str: ...
    #: **080, stage 1.** A live, `keepUpToDate`-shaped minute-bar series.
    #: `on_update(bars)` fires with the FULL current bar list on every
    #: revision — never just the delta — because `vwap_from_bars`/
    #: `cumulative_volume`/`rvol_at` all need the whole series, not one bar.
    #: A fixture answers this synchronously and instantly, exactly as every
    #: other method here does; the live client's version genuinely stays
    #: open until cancelled.
    def open_price_stream(
        self, c: Contract, on_update: Callable[[Sequence[Bar]], None]
    ) -> StreamHandle: ...
    def playbook_for(self, c: Contract) -> str: ...


@dataclass
class AttachResult:
    """What a caller gets back from STAGE 1. **An attach that failed at
    steps 2-4 is still an attach**, and this object is the only place that
    distinction is expressed.

    **080: `context`/`rail`/`partial` are gone from this object.** They held
    stage 2's output, and stage 2 is no longer one call this function makes
    and waits on — it is `Stage2Inputs`/`compute_context_and_rail`, driven by
    `app.py` from callbacks that land after this function has already
    returned. A caller wanting the context block no longer reads it off
    `AttachResult` at all.
    """

    symbol: str
    origin: str
    attached: bool = False
    contract: Optional[Contract] = None
    #: Set only when step 1 refused. Carries the candidates, never a choice.
    ambiguous: list[Contract] = field(default_factory=list)
    refusal: str = ""
    #: **070 §6.** Set only when step 2 finds the SAME contract inside
    #: `COOLDOWN_S` of its last historical fetch. Holds the remaining time
    #: (`"11s"`), never a bare int — every other rendered-reason field on
    #: this object is already a display string, and a lone `int` here would
    #: be the one field a caller has to remember to format.
    queued: str = ""
    slot_state: str = ""
    tape: str = ""
    playbook: str = ""

    @property
    def qualified(self) -> bool:
        """True only when exactly one contract was chosen. Refusal D asserts
        this is False for an ambiguous ticker — **no contract was qualified**,
        not 'the best one was'."""
        return self.contract is not None


def attach(symbol: str, md: MarketData, *, origin: str = "typed") -> AttachResult:
    if origin not in ORIGINS:
        raise ValueError(f"origin must be one of {ORIGINS}, got {origin!r}")
    r = AttachResult(symbol=symbol.strip().upper(), origin=origin)

    # ---- step 1: resolve. THE ONLY BLOCKING STEP ---------------------------
    try:
        candidates = list(md.resolve(r.symbol))
    except Exception as exc:                       # noqa: BLE001 - reported, not raised
        r.refusal = f"contract lookup failed ({type(exc).__name__})"
        return r
    if not candidates:
        r.refusal = "no contract found"
        return r
    if len(candidates) > 1:
        # `tws_order`'s wording is the model, and the behaviour is the point:
        # picking the most liquid is a well-formed value answering a different
        # question, and it would be silently right most of the time -- which is
        # exactly what makes it dangerous.
        r.ambiguous = candidates
        r.refusal = (f"resolved to {len(candidates)} contracts - ambiguous, "
                     f"refusing to guess")
        return r
    r.contract = candidates[0]

    # ---- step 2: the tick slot, BEFORE any historical request --------------
    cooldown = md.cooldown_remaining_s(r.symbol)
    if cooldown > 0:
        # **070 §6, ruled by the mockup: refuses BEFORE step 3, not merely
        # renders differently after it.** `cooldown_remaining_s` and `warm`'s
        # own pacing guard read the same `_note_fetch` clock — but
        # `dailies_on()` and its siblings (below) fall back to their own
        # live request whenever `warm()` did not populate the cache, and
        # that fallback path calls `md.daily_bars()` etc. directly, with no
        # pacing check of its own. Letting step 3 run here would spend a
        # second, unguarded round of the same requests `warm()`'s check
        # exists to keep under IBKR's limit — so the whole gather stops here
        # instead, and the panel says how long until it can run.
        r.queued = f"{cooldown}s"
        return r
    in_use = md.tick_slots_in_use()
    r.slot_state = (f"{in_use}/{TICK_SLOTS} slots used"
                    if in_use < TICK_SLOTS
                    else f"no tick slot - detach one of {in_use} to free it")

    # **080.** Stage 2 (the historical requests behind `ADR% used`/`RVOL`/
    # `VWAP`) no longer runs here at all — `app.py` dispatches it, and the
    # live price stream, the instant this function returns `r.contract`.
    # Nothing below this line waits on a historical request.

    # ---- step 3: the tape. Never gated on a historical request ------------
    if r.slot_state.startswith("no tick slot"):
        r.tape = "absent - no free tick slot"
    else:
        try:
            r.tape = md.open_tick_stream(r.contract)
        except Exception as exc:                   # noqa: BLE001
            # The MESSAGE, not the class name. The first live run rendered
            # `absent - RuntimeError`, which says nothing a reader can act on;
            # the exception already carried "no tape components in core".
            r.tape = f"absent - {_reason(exc)}"

    # ---- step 4: the playbook ----------------------------------------------
    try:
        r.playbook = md.playbook_for(r.contract) or "no trigger level declared"
    except Exception:                              # noqa: BLE001
        r.playbook = "no trigger level declared"

    r.attached = True
    return r


@dataclass
class Stage2Inputs:
    """**080.** Every independent piece of data the four value rows and the
    LEVELS rail can be built from — each starting absent and arriving on its
    own schedule. `app.py` owns one instance per attach, mutates it as each
    role/stream lands, and calls `compute_context_and_rail(inp)` again after
    every mutation.

    **A field being `None` (and its `_failed` sibling being `""`) IS the
    pending state** — there is no separate boolean, because a third state
    ("pending" vs "landed" vs "failed") only needs two facts (value, error)
    to be fully determined, and a redundant flag is a second place those two
    facts could disagree.

    **`today`/`sector_today` are never one-shot.** They are replaced by the
    `keepUpToDate` price streams (080, stage 1) — every stream update
    replaces the WHOLE list here (never appended to), because a forming bar
    is REVISED IN PLACE (008b's own finding: 344 of 376 updates revised the
    forming minute, only 32 appended a new one), and `on_update` already
    hands back the full current series for exactly that reason.
    """

    has_sector: bool = False
    today: Optional[Sequence[Bar]] = None
    today_failed: str = ""
    sector_today: Optional[Sequence[Bar]] = None
    sector_today_failed: str = ""
    rth_dailies: Optional[Sequence[Bar]] = None
    rth_dailies_failed: str = ""
    sessions: Optional[Sequence[Sequence[Bar]]] = None
    sessions_failed: str = ""
    sector_sessions: Optional[Sequence[Sequence[Bar]]] = None
    sector_sessions_failed: str = ""


def _adr_terms(rth_dailies: Sequence[Bar]) -> tuple[Measured, Measured, float]:
    """`(pct, dol, todays_open)` — the shared arithmetic `ADR% used` and the
    LEVELS rail's `adr_dol` both need from the same `rth_dailies` series.
    Split out so `compute_context_and_rail` computes it once, not twice."""
    todays_open = rth_dailies[-1].open
    pct = adr_pct(rth_dailies)
    dol = adr_dollar(pct, todays_open)
    return pct, dol, todays_open


def compute_context_and_rail(
    inp: Stage2Inputs,
) -> tuple[dict[str, Measured], dict[str, Measured]]:
    """**080.** The pure recompute stage 2 now runs on. Called every time one
    more of `inp`'s fields changes; returns whichever rows are CURRENTLY
    computable from what has landed so far. **A row absent from the returned
    `context` dict is pending — not refused, not zero.** `app.py` merges new
    keys into the record's existing context, never removing one that already
    landed, because `inp`'s fields only ever go from absent to present or
    failed, never back.

    **Each row refuses on its own** — a failure in the sessions request must
    not blank `ADR% used`, which reads a different input entirely. This is
    the same guarantee `_context_block` (078/B-130's home, retired by this
    task) gave the old one-shot gather; here it falls out of each branch
    below reading only its own inputs.
    """
    out: dict[str, Measured] = {}

    # --- Last $ / VWAP -- the symbol price stream alone ---------------------
    if inp.today_failed:
        out["Last $"] = Measured.absent(inp.today_failed)
        out["VWAP"] = Measured.absent(inp.today_failed)
        out["cum vol"] = Measured.absent(inp.today_failed)
    elif inp.today:
        out["Last $"] = Measured(value=inp.today[-1].close, sample="last trade",
                                 unit=Unit.DOLLAR, basis=INTRADAY_BASIS)
        out["VWAP"] = vwap_from_bars(inp.today)
        out["cum vol"] = cumulative_volume(inp.today)
    # else: the stream has not delivered its first payload yet -- pending.

    # --- ADR% used -- self-sufficient from rth_dailies alone -----------------
    #
    # **`price` is `rth_dailies[-1].close`, the daily bar's own close, NOT
    # the price stream's** — unchanged from the retired `_context_block`.
    # `adr_used`'s existing call is reused verbatim; only WHEN it fires
    # changed, not what it is fed.
    dol: Optional[Measured] = None
    if inp.rth_dailies_failed:
        out["ADR% used"] = Measured.absent(inp.rth_dailies_failed)
    elif inp.rth_dailies:
        pct, dol, todays_open = _adr_terms(inp.rth_dailies)
        out["ADR% used"] = adr_used(inp.rth_dailies[-1].close, todays_open, dol)
        # **The SMA stack is UNRULED, computed and recorded, never
        # displayed** (unchanged from the retired `_context_block`) — the
        # mockup keeps it off this panel; `app.py`'s `CONTEXT_ORDER` is what
        # keeps it off screen, not this function.
        sma_price = inp.rth_dailies[-1].close
        for n in (10, 20, 50):
            out[f"ext {n}"] = extension_in_adr(sma_price, sma(inp.rth_dailies, n), dol)
    # else: pending.

    # --- RVOL -- own reading needs sessions AND the price stream -----------
    own: Optional[Measured] = None
    if inp.sessions_failed:
        own = Measured.absent(inp.sessions_failed)
        out["RVOL"] = own
    elif inp.sessions and inp.today:
        own = rvol_at(inp.today, rvol_curve(inp.sessions))
        out["RVOL"] = own
    elif inp.sessions is not None and not inp.today:
        # Sessions landed with no bars at all -- a real, named empty result,
        # not a pending state; `rvol_at` already refuses this correctly.
        own = Measured.absent("no bars today") if inp.today is not None else None
        if own is not None:
            out["RVOL"] = own
    # else: pending on `sessions`.

    # --- RVOL_rel -- NEVER 1.0. Independent readings, independent landing --
    if not inp.has_sector:
        if own is not None:
            out["RVOL_rel"] = Measured.absent("no sector mapping")
        out["RVOL_sector"] = Measured.absent("no sector mapping")
    else:
        if inp.sector_sessions_failed or inp.sector_today_failed:
            reason = inp.sector_sessions_failed or inp.sector_today_failed
            if own is not None:
                out["RVOL_rel"] = Measured.absent(reason)
            out["RVOL_sector"] = Measured.absent(reason)
        elif inp.sector_sessions and inp.sector_today:
            sector_rvol = rvol_at(inp.sector_today, rvol_curve(inp.sector_sessions))
            out["RVOL_sector"] = sector_rvol
            if own is not None:
                out["RVOL_rel"] = rvol_rel(own, sector_rvol)
        # else: pending on the sector's own sessions/stream.

    # --- the level rail. Refuses alongside ADR% used, not merely pending ---
    #
    # **A FAILED `rth_dailies` still produces a rail** — `level_rail` is
    # called with an absent `adr_dol` and `prev_day`/year-high/low all
    # `None`, exactly as the retired `_context_block` did — so `round` (and
    # every other rail value spanned by ADR $) refuses BY NAME rather than
    # simply never appearing. Only the genuinely PENDING case (neither
    # landed nor failed yet) leaves `rail` empty.
    rail: dict[str, Measured] = {}
    if inp.rth_dailies_failed:
        today = inp.today or ()
        premarket = [b for b in today if _clock(b.ts) < "09:30"]
        opening_5 = [b for b in today if "09:30" <= _clock(b.ts) < "09:35"]
        opening_15 = [b for b in today if "09:30" <= _clock(b.ts) < "09:45"]
        rail = level_rail(
            prev_day=None, premarket=premarket,
            opening_5=opening_5, opening_15=opening_15,
            session_clock=_clock(today[-1].ts) if today else None,
            vwap=out.get("VWAP", Measured.absent("no session bars")),
            year_high=None, year_low=None,
            price=today[-1].close if today else 0.0,
            adr_dol=Measured.absent(inp.rth_dailies_failed))
    elif inp.rth_dailies:
        if dol is None:
            _, dol, _ = _adr_terms(inp.rth_dailies)
        yh = max(b.high for b in inp.rth_dailies)
        yl = min(b.low for b in inp.rth_dailies)
        prior = inp.rth_dailies      # PRIOR_DAY_BASIS shares rth_dailies -- both RTH.
        prev_day = prior[-2] if len(prior) >= 2 else None
        today = inp.today or ()
        premarket = [b for b in today if _clock(b.ts) < "09:30"]
        opening_5 = [b for b in today if "09:30" <= _clock(b.ts) < "09:35"]
        opening_15 = [b for b in today if "09:30" <= _clock(b.ts) < "09:45"]
        rail = level_rail(
            prev_day=prev_day, premarket=premarket,
            opening_5=opening_5, opening_15=opening_15,
            session_clock=_clock(today[-1].ts) if today else None,
            vwap=out.get("VWAP", Measured.absent("no session bars")),
            year_high=yh, year_low=yl,
            price=today[-1].close if today else prior[-1].close,
            adr_dol=dol)
    # else: rth_dailies is genuinely pending -- the rail waits with it.

    return out, rail


def _clock(ts: str) -> str:
    return ts[11:16] if len(ts) >= 16 else ts


def _reason(exc: BaseException) -> str:
    """**Pacing is a display state, not an error** (S010 part 2).

    A pacing refusal that renders as a crash teaches you to distrust the
    terminal; one that renders as `unavailable — pacing limit, retry in 42s`
    teaches you to wait. The distinction is carried by the exception's own
    message, so a future client can raise something richer without changing
    this.
    """
    msg = str(exc).strip()
    return msg or f"{type(exc).__name__}"

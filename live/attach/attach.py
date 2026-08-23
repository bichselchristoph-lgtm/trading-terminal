"""The attach sequence — S010 part 1, `SPEC.md` §6b.1a-seq.

**Attach does five things and they are not one operation.** Three of them can
fail independently, and **each failure must leave the others working.** That is
the whole design, and it is why this is a sequence with a result object rather
than a function that returns a symbol or raises.

    | # | step                          | blocking | on failure                    |
    |---|-------------------------------|----------|-------------------------------|
    | 1 | resolve the contract          | YES      | ambiguous -> render, ask      |
    | 2 | check the tick slot           | no       | render NOW, name what to drop |
    | 3 | 4-6 historical requests, GATHERED CONCURRENTLY | no | per-row unavailable(reason) |
    | 4 | open the tick-by-tick stream  | no       | attach SUCCEEDS, tape absent  |
    | 5 | bind the playbook             | no       | `no trigger level declared`   |

**Step 2 precedes step 3 deliberately.** With no slot you should learn that in
the first frame — not after three historical requests have been spent against a
60-per-10-minutes budget on a symbol you are about to detach.

**Step 4 does not gate step 3, and that ordering is the point of the slice.** A
symbol with no free tick slot still yields ADR, ATR, extension, the level rail,
both RVOLs and session VWAP — everything sizing will need. **The tape is an
enrichment, not a precondition**, and an attach that refused wholesale because
one of five slots was busy would be a worse terminal than one that says so and
carries on.

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
from typing import Optional, Protocol, Sequence

from core.indicators.context import (ADR_BASIS, ATR_BASIS, Bar, Measured,
                                     PRIOR_DAY_BASIS, SMA_BASIS, SessionBasis,
                                     adr_available, adr_dollar, adr_pct, atr_d14,
                                     cumulative_volume, extension_in_adr,
                                     level_rail, rvol_at, rvol_curve,
                                     rvol_rel, sma, vwap_from_bars)

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
    #: **058 Part 2.** Fire every independent historical request this attach
    #: needs, CONCURRENTLY, before the per-role methods below are read. A
    #: fixture that never implements this as anything but a no-op is
    #: unaffected — each per-role method still answers on its own; `warm` is
    #: an optimisation the live client makes real, not a new contract the
    #: numbers depend on.
    def warm(self, c: Contract) -> None: ...
    def daily_bars(self, c: Contract, basis: SessionBasis) -> Sequence[Bar]: ...
    def intraday_sessions(self, c: Contract) -> Sequence[Sequence[Bar]]: ...
    def today_minutes(self, c: Contract) -> Sequence[Bar]: ...
    def sector_today_minutes(self, c: Contract) -> Optional[Sequence[Bar]]: ...
    def sector_sessions(self, c: Contract) -> Optional[Sequence[Sequence[Bar]]]: ...
    def open_tick_stream(self, c: Contract) -> str: ...
    def playbook_for(self, c: Contract) -> str: ...


@dataclass
class AttachResult:
    """What a caller gets back. **An attach that failed at steps 2-5 is still an
    attach**, and this object is the only place that distinction is expressed."""

    symbol: str
    origin: str
    attached: bool = False
    contract: Optional[Contract] = None
    #: Set only when step 1 refused. Carries the candidates, never a choice.
    ambiguous: list[Contract] = field(default_factory=list)
    refusal: str = ""
    slot_state: str = ""
    tape: str = ""
    playbook: str = ""
    context: dict[str, Measured] = field(default_factory=dict)
    rail: dict[str, Measured] = field(default_factory=dict)
    #: **058 Part 3.** "N of M rows unavailable" when the gather completed
    #: with SOME requests refusing. Empty when everything measured. Tenet 3
    #: — status inherits from the weakest — has to be RENDERED, not merely
    #: true: four values and two refusals must not be indistinguishable from
    #: a complete attach of an illiquid name.
    partial: str = ""

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
        r.slot_state = f"queued - {cooldown}s"
    else:
        in_use = md.tick_slots_in_use()
        r.slot_state = (f"{in_use}/{TICK_SLOTS} slots used"
                        if in_use < TICK_SLOTS
                        else f"no tick slot - detach one of {in_use} to free it")

    # ---- step 3: three historical requests, each failing alone -------------
    r.context, r.rail = _context_block(r.contract, md)

    # ---- step 4: the tape. DOES NOT GATE STEP 3 ---------------------------
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

    # ---- step 5: the playbook ---------------------------------------------
    try:
        r.playbook = md.playbook_for(r.contract) or "no trigger level declared"
    except Exception:                              # noqa: BLE001
        r.playbook = "no trigger level declared"

    # **058 Part 3.** A screen-level statement that the gather completed
    # with refusals — the per-row `— (reason)` cells already say WHICH rows,
    # this says the attach as a whole is not a clean one, so a reader
    # scanning the header cannot mistake a partial attach for a complete one.
    values = {**r.context, **r.rail}
    refused = [k for k, v in values.items() if getattr(v, "ok", True) is False]
    if refused:
        r.partial = f"{len(refused)} of {len(values)} rows unavailable"

    r.attached = True
    return r


def _context_block(c: Contract, md: MarketData) -> tuple[dict[str, Measured], dict[str, Measured]]:
    """The three requests. **Each row refuses on its own** — a failure in the
    intraday request must not blank ADR, which came from a different call."""
    out: dict[str, Measured] = {}

    # --- 058 Part 2: fire every independent historical request at once -----
    #
    # A failure here is not fatal — every fetch below still tries its own
    # live request if warming did not populate it (a `Fake` never populates
    # anything; it is a no-op). That is Refusal A extended to the gather
    # rather than a new failure mode: one dead round trip must not cost the
    # rows that a second, working round trip could still answer.
    try:
        md.warm(c)
    except Exception:                              # noqa: BLE001
        pass

    # --- request 1: dailies, ONCE PER DISTINCT BASIS -----------------------
    #
    # **038 Part 1. This used to be one request at `use_rth=True` feeding ADR,
    # the SMA stack, PDH/PDL and ATR14 alike** — and that is precisely how
    # `ATR14` came to read `13.14` against a true ~`15.6`. ATR's true range
    # spans the prior close, so the gap is the measurement, so it needs the ETH
    # series; ADR has no gap term at all and is RTH by definition.
    #
    # **Memoised on the flag, not on the indicator.** Two indicators sharing a
    # basis share the request — IBKR's pacing budget is ~60 historical requests
    # per 10 minutes (§6b.1b) and an attach that issued one per indicator would
    # spend it. But each indicator still ASKS with its own constant, so flipping
    # one basis moves that indicator alone and cannot silently drag another with
    # it.
    _daily_cache: dict[bool, list[Bar]] = {}
    _daily_failed: dict[bool, str] = {}

    def dailies_on(basis: SessionBasis) -> list[Bar]:
        if basis.use_rth in _daily_cache:
            return _daily_cache[basis.use_rth]
        if basis.use_rth in _daily_failed:
            return []
        try:
            bars = list(md.daily_bars(c, basis))
        except Exception as exc:                   # noqa: BLE001
            _daily_failed[basis.use_rth] = _reason(exc)
            return []
        _daily_cache[basis.use_rth] = bars
        return bars

    def daily_why(basis: SessionBasis) -> str:
        return _daily_failed.get(basis.use_rth, "no daily bars")

    rth_dailies = dailies_on(ADR_BASIS)
    eth_dailies = dailies_on(ATR_BASIS)

    # **ADR% and ADR%avail — RTH.** Each row still refuses on its own; a failure
    # on the ETH request must not blank ADR and vice versa.
    #
    # **042 Part 3 deletes four rows and adds one.** `ADR used`, `ADR $`,
    # `room up` and `room down` leave the panel — `room up`/`room down`
    # measured the same quantity as `ADR used` in dollars and invited being read
    # as `clear for`, which is distance to the next obstacle and a different
    # question. `ADR%avail` is the reading Christoph actually takes.
    #
    # **`dol` IS STILL COMPUTED AND IS NOT A DEAD LOCAL.** `ADR $` leaves the
    # PANEL; the value does not leave the system. `adr_available` divides by it
    # and `level_rail` spans `round` with it. 042: *"`ADR` itself is not
    # deleted... only the four display rows go."* Dropping the computation would
    # silently blank `round` as well, which is the kind of second-order deletion
    # a row-removal task invites.
    if rth_dailies:
        todays_open = rth_dailies[-1].open
        price = rth_dailies[-1].close
        pct = adr_pct(rth_dailies)
        dol = adr_dollar(pct, todays_open)
        out["ADR%"] = pct
        out["ADR%avail"] = adr_available(price, todays_open, dol)
    else:
        why = daily_why(ADR_BASIS)
        for k in ("ADR%", "ADR%avail"):
            out[k] = Measured.absent(why)
        dol = Measured.absent(why)
        price = 0.0

    # **The SMA stack is UNRULED by 038** and keeps the RTH basis it had. It asks
    # with `SMA_BASIS` rather than reusing `rth_dailies` directly, so a future
    # ruling changes one constant and nothing else.
    sma_dailies = dailies_on(SMA_BASIS)
    if sma_dailies:
        sma_price = sma_dailies[-1].close
        for n in (10, 20, 50):
            out[f"ext {n}"] = extension_in_adr(sma_price, sma(sma_dailies, n), dol)
    else:
        for n in (10, 20, 50):
            out[f"ext {n}"] = Measured.absent(daily_why(SMA_BASIS))

    # **ATR20 — ETH.** 038 moved the basis; 065/B-091 moves the period, ruled
    # twice and confirmed directly by Christoph on 2026-08-22: one ATR, 20-day,
    # ETH. `atr_d14` keeps its name — `ATR_DEFAULT_N` in `core/indicators/context.py`
    # is what actually changed, to 20 — but the RENDERED key changes with it,
    # because a label one character wrong is the defect this project keeps
    # cataloguing.
    out["ATR20"] = atr_d14(eth_dailies) if eth_dailies         else Measured.absent(daily_why(ATR_BASIS))

    # --- request 3: today, from the open -----------------------------------
    try:
        today = list(md.today_minutes(c))
    except Exception as exc:                       # noqa: BLE001
        today = []
        out["VWAP"] = Measured.absent(_reason(exc))
        out["cum vol"] = Measured.absent(_reason(exc))
    if today:
        out["VWAP"] = vwap_from_bars(today)
        out["cum vol"] = cumulative_volume(today)

    # --- request 2: 20 sessions intraday -> the RVOL curve ------------------
    try:
        sessions = list(md.intraday_sessions(c))
    except Exception as exc:                       # noqa: BLE001
        sessions = []
        out["RVOL"] = Measured.absent(_reason(exc))
    if sessions:
        out["RVOL"] = rvol_at(today, rvol_curve(sessions)) if today else \
            Measured.absent("no bars today")

    # --- RVOL_rel. NEVER 1.0 ------------------------------------------------
    sector_rvol: Optional[Measured] = None
    if c.sector_etf:
        try:
            s_sessions = md.sector_sessions(c)
            s_today = md.sector_today_minutes(c)
            if s_sessions and s_today:
                sector_rvol = rvol_at(list(s_today), rvol_curve(list(s_sessions)))
        except Exception as exc:                   # noqa: BLE001
            sector_rvol = Measured.absent(_reason(exc))
    out["RVOL_rel"] = rvol_rel(out.get("RVOL", Measured.absent("no RVOL")), sector_rvol)

    # --- the level rail -----------------------------------------------------
    #
    # **058 Part 1. 52wH/52wL come off `rth_dailies` — no second request.**
    # `daily_bars(c, ADR_BASIS)` now fetches a full year of RTH dailies (not
    # 60D), because ADR%/the SMA stack/PDH-PDL only ever read the TAIL of
    # whatever they are given (`adr_pct`/`sma` slice `[-n:]`), so extending
    # the window changes nothing they compute — and the same series already
    # holds everything 52wH/52wL need. `year_high_low` is retired as a
    # separate `MarketData` call for exactly this reason: the two "requests"
    # were always the same RTH daily series at two different windows.
    if rth_dailies:
        yh, yl = (max(b.high for b in rth_dailies), min(b.low for b in rth_dailies))
    else:
        yh = yl = None
    # **PDH/PDL come from the RTH dailies** (038 Part 1). On ETH bars `PDL`
    # would be the prior session's extended-hours low — which is `AML`, a
    # different level wearing PDL's name. Confirmed on QQQ 2026-08-13, where the
    # ETH low of 717.37 sat in the early pre-market.
    prior = dailies_on(PRIOR_DAY_BASIS)
    prev_day = prior[-2] if len(prior) >= 2 else None
    premarket = [b for b in today if _clock(b.ts) < "09:30"]
    # 042 Part 1. Two windows, and the 15 CONTAINS the 5 — which is what makes
    # `ORH15 >= ORH5` and `ORL15 <= ORL5` hold by construction rather than by
    # luck. Sliced here rather than inside `level_rail` so `core` keeps taking
    # bars and never a clock convention.
    opening_5 = [b for b in today if "09:30" <= _clock(b.ts) < "09:35"]
    opening_15 = [b for b in today if "09:30" <= _clock(b.ts) < "09:45"]
    rail = level_rail(prev_day=prev_day, premarket=premarket,
                      opening_5=opening_5, opening_15=opening_15,
                      session_clock=_clock(today[-1].ts) if today else None,
                      vwap=out.get("VWAP", Measured.absent("no session bars")),
                      year_high=yh, year_low=yl,
                      price=today[-1].close if today else (prior[-1].close if prior else 0.0),
                      # `ADR $` no longer renders (042 Part 3) so it is no
                      # longer in `out` — passed directly from the local.
                      adr_dol=dol)
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

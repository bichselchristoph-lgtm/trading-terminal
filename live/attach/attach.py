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

from core.indicators.context import (ADR_BASIS, Bar, INTRADAY_BASIS, Measured,
                                     PRIOR_DAY_BASIS, SMA_BASIS, SessionBasis,
                                     Unit, adr_dollar, adr_pct, adr_used,
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
    #: **070 §6.** Set only when step 2 finds the SAME contract inside
    #: `COOLDOWN_S` of its last historical fetch. Holds the remaining time
    #: (`"11s"`), never a bare int — every other rendered-reason field on
    #: this object is already a display string, and a lone `int` here would
    #: be the one field a caller has to remember to format.
    queued: str = ""
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

    # ---- step 3: three historical requests, each failing alone -------------
    r.context, r.rail, warm_failure = _context_block(r.contract, md)

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
    # **078/B-130.** `warm_failure` and `refused` are independent facts and
    # neither may silently swallow the other. A row can refuse for reasons
    # that have nothing to do with `warm()` (PMH/PML with no pre-market
    # bars yet, for instance) — if that alone suppressed the degraded-gather
    # sentence, the one morning both happen together is exactly the morning
    # this task exists to make legible, and it would go quiet again.
    if refused and warm_failure:
        r.partial = (f"{len(refused)} of {len(values)} rows unavailable "
                     f"(gather degraded - {warm_failure})")
    elif refused:
        # **058 Part 3.** A screen-level statement that the gather
        # completed with refusals — the per-row `— (reason)` cells already
        # say WHICH rows, this says the attach as a whole is not a clean
        # one, so a reader scanning the header cannot mistake a partial
        # attach for a complete one.
        r.partial = f"{len(refused)} of {len(values)} rows unavailable"
    elif warm_failure:
        # `warm()` failed but every row still measured — each one fell
        # back to its own individual, unguarded request and got there
        # anyway, so `refused` above is empty and this attach would
        # otherwise look completely clean. It was not: reusing the SAME
        # field, the SAME rendered row and the SAME `flagged, not an
        # error` suffix `refused` already uses (no new token, no new
        # colour, no new row — 078 §3) — just a different sentence for a
        # different cause, since "N of M rows unavailable" would be false
        # here (every row DID measure; the fast, guarded path did not).
        r.partial = f"gather degraded - {warm_failure}"

    r.attached = True
    return r


def _context_block(c: Contract, md: MarketData) -> tuple[dict[str, Measured], dict[str, Measured], str]:
    """The three requests. **Each row refuses on its own** — a failure in the
    intraday request must not blank ADR, which came from a different call.

    **078/B-130: the third return value.** `warm()`'s own failure used to be
    a bare `except Exception: pass` — swallowed with no trace anywhere. 075
    measured this live: `warm()` timed out on 3 of 6 AMZN attaches, every
    per-role read then fell back to its own individual request, and every
    one of those fallbacks succeeded — so `refused` (below, in `attach()`)
    stayed empty and the attach LOOKED clean. It was not: it took the
    unguarded, pre-058 sequential path for 70-83 extra seconds, and nothing
    on screen or in any log said so. `warm_failure` carries the reason
    (empty string when `warm()` did not raise) so `attach()` can surface it
    even when every row still measured successfully.
    """
    out: dict[str, Measured] = {}
    warm_failure = ""

    # --- 058 Part 2: fire every independent historical request at once -----
    #
    # A failure here is not fatal — every fetch below still tries its own
    # live request if warming did not populate it (a `Fake` never populates
    # anything; it is a no-op). That is Refusal A extended to the gather
    # rather than a new failure mode: one dead round trip must not cost the
    # rows that a second, working round trip could still answer.
    try:
        md.warm(c)
    except Exception as exc:                       # noqa: BLE001
        warm_failure = _reason(exc)

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

    # **ADR% used — RTH, the panel's only ADR/ATR row.** 070, ruled by Christoph
    # 2026-08-23: the context block carries `ADR% used` and NO other ADR
    # metric, and NO ATR anywhere in this panel — TRADE's stop selector is
    # ATR's only surface in the whole terminal. `ADR%avail`, `ADR $`, `room
    # up`/`room down` and any ATR row all leave `out` entirely here, not merely
    # `CONTEXT_ORDER` — B-028 is exactly a value that kept reaching the
    # renderer after its row was deleted, and a field absent from this
    # dict cannot repeat that by accident.
    #
    # **`adr_used` is the existing function, not a new formula.** 070 Part 2:
    # `ADR%avail = 100 - adr_used`, so the row this task adds is what
    # `adr_available` was already computing internally before returning its
    # complement — reused directly rather than re-derived.
    #
    # **The ETH daily request that fed ATR is also gone.** Nothing else in this
    # block consumed `eth_dailies`; keeping the fetch alive for a value nobody
    # reads would spend part of IBKR's pacing budget for nothing. TRADE's own
    # task adds its own request when it needs one — this function serves
    # ATTACHED specifically, not a shared cache of everything any panel might
    # ever want.
    #
    # **`dol` IS STILL COMPUTED AND IS NOT A DEAD LOCAL.** `level_rail` spans
    # `round` with it, and `adr_used` divides by it. Only the display rows go.
    if rth_dailies:
        todays_open = rth_dailies[-1].open
        price = rth_dailies[-1].close
        pct = adr_pct(rth_dailies)
        dol = adr_dollar(pct, todays_open)
        out["ADR% used"] = adr_used(price, todays_open, dol)
    else:
        why = daily_why(ADR_BASIS)
        out["ADR% used"] = Measured.absent(why)
        dol = Measured.absent(why)
        price = 0.0

    # **The SMA stack is UNRULED by 038, computed and recorded, never
    # displayed** — the `ATTACHED` mockup v1.0 §2 removes it from this panel
    # on the same footing as ATR ("Chart work"), but does not say the
    # computation stops; `live/tui/app.py`'s `CONTEXT_ORDER` is what actually
    # keeps it off screen, not this function.
    sma_dailies = dailies_on(SMA_BASIS)
    if sma_dailies:
        sma_price = sma_dailies[-1].close
        for n in (10, 20, 50):
            out[f"ext {n}"] = extension_in_adr(sma_price, sma(sma_dailies, n), dol)
    else:
        for n in (10, 20, 50):
            out[f"ext {n}"] = Measured.absent(daily_why(SMA_BASIS))

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

    # **070. `VWAP_ext` — how far price sits above/below VWAP, in dollars.**
    # `ATTACHED` mockup v1.0 §1: `VWAP $730.68 · +$2.46`. Not a new VWAP
    # statistic — `vwap_from_bars` is untouched — this is the renderer's own
    # derived value (today's latest close minus VWAP), scoped to `attach.py`
    # since `touches:` names the ATTACHED renderer, not the VWAP statistic.
    if today and out["VWAP"].ok:
        out["VWAP_ext"] = Measured(value=today[-1].close - out["VWAP"].value,
                                   sample="price - VWAP", unit=Unit.DOLLAR,
                                   basis=INTRADAY_BASIS)
    else:
        out["VWAP_ext"] = Measured.absent(out["VWAP"].unavailable)

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
    # **070. Exposed under its own key, not left a dead local.** `ATTACHED`
    # mockup v1.0 §1 folds the sector's own RVOL into the same line as
    # `RVOL_rel` (`avg 0.86x`) — it was already computed here for
    # `rvol_rel`'s sake and simply never reached `out` before this task.
    out["RVOL_sector"] = sector_rvol if sector_rvol is not None \
        else Measured.absent("no sector mapping")

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
    return out, rail, warm_failure


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

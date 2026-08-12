"""The attach sequence — S010 part 1, `SPEC.md` §6b.1a-seq.

**Attach does five things and they are not one operation.** Three of them can
fail independently, and **each failure must leave the others working.** That is
the whole design, and it is why this is a sequence with a result object rather
than a function that returns a symbol or raises.

    | # | step                          | blocking | on failure                    |
    |---|-------------------------------|----------|-------------------------------|
    | 1 | resolve the contract          | YES      | ambiguous -> render, ask      |
    | 2 | check the tick slot           | no       | render NOW, name what to drop |
    | 3 | three historical requests     | no       | per-row unavailable(reason)   |
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

from core.indicators.context import (Bar, Measured, adr_dollar, adr_pct,
                                     adr_used, atr_d14, cumulative_volume,
                                     extension_in_adr, level_rail, room_left,
                                     rvol_at, rvol_curve, rvol_rel, sma,
                                     vwap_from_bars)

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
    def daily_bars(self, c: Contract) -> Sequence[Bar]: ...
    def intraday_sessions(self, c: Contract) -> Sequence[Sequence[Bar]]: ...
    def today_minutes(self, c: Contract) -> Sequence[Bar]: ...
    def sector_today_minutes(self, c: Contract) -> Optional[Sequence[Bar]]: ...
    def sector_sessions(self, c: Contract) -> Optional[Sequence[Sequence[Bar]]]: ...
    def open_tick_stream(self, c: Contract) -> str: ...
    def playbook_for(self, c: Contract) -> str: ...
    def year_high_low(self, c: Contract) -> tuple[Optional[float], Optional[float]]: ...


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
            r.tape = f"absent - {type(exc).__name__}"

    # ---- step 5: the playbook ---------------------------------------------
    try:
        r.playbook = md.playbook_for(r.contract) or "no trigger level declared"
    except Exception:                              # noqa: BLE001
        r.playbook = "no trigger level declared"

    r.attached = True
    return r


def _context_block(c: Contract, md: MarketData) -> tuple[dict[str, Measured], dict[str, Measured]]:
    """The three requests. **Each row refuses on its own** — a failure in the
    intraday request must not blank ADR, which came from a different call."""
    out: dict[str, Measured] = {}

    # --- request 1: dailies ------------------------------------------------
    try:
        dailies = list(md.daily_bars(c))
    except Exception as exc:                       # noqa: BLE001
        dailies = []
        why = _reason(exc)
        for k in ("ADR%", "ADR $", "ADR used", "room up", "room down",
                  "ATR14", "ext 10", "ext 20", "ext 50"):
            out[k] = Measured.absent(why)

    if dailies:
        todays_open = dailies[-1].open
        price = dailies[-1].close
        pct = adr_pct(dailies)
        dol = adr_dollar(pct, todays_open)
        up, down = room_left(price, todays_open, dol)
        out["ADR%"] = pct
        out["ADR $"] = dol
        out["ADR used"] = adr_used(price, todays_open, dol)
        out["room up"], out["room down"] = up, down
        out["ATR14"] = atr_d14(dailies)
        for n in (10, 20, 50):
            out[f"ext {n}"] = extension_in_adr(price, sma(dailies, n), dol)

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
    try:
        yh, yl = md.year_high_low(c)
    except Exception:                              # noqa: BLE001
        yh = yl = None
    prev_day = dailies[-2] if len(dailies) >= 2 else None
    premarket = [b for b in today if _clock(b.ts) < "09:30"]
    opening = [b for b in today if "09:30" <= _clock(b.ts) < "09:35"]
    rail = level_rail(prev_day=prev_day, premarket=premarket, opening_range=opening,
                      vwap=out.get("VWAP", Measured.absent("no session bars")),
                      year_high=yh, year_low=yl,
                      price=today[-1].close if today else (dailies[-1].close if dailies else 0.0),
                      adr_dol=out.get("ADR $", Measured.absent("no ADR $")))
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

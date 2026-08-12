"""The live `MarketData` — the only thing in S010 that touches a broker.

**Everything else in the slice is pure and was built and tested against fixtures
while the `019` capture held the only client.** This module is the seam, and it
is deliberately thin: it turns IBKR calls into `core.indicators.context.Bar`
and nothing else. No arithmetic happens here, so nothing here can be wrong in a
way a fixture test would not catch.

**`ib_async`, never `ib_insync`.** The latter is unmaintained. `live/feeds.py` in
the predecessor still imports it, which is legacy to migrate and not a pattern
to copy — and S010's *Do not* list forbids adopting it.

**`readonly=True`.** A context block has no business being able to place an
order, and in this workspace only `tws_order` may.

----

**`use_rth` is passed explicitly at EVERY call site, and a test asserts it.**

`SPEC.md` §010 2f: *`reqHistoricalData` and `reqHistoricalTicks` both default to
`useRTH=True`, and getting it wrong returns RTH-only data silently* — no error,
just a different number. That is the worst available failure mode, so the
parameter is never omitted and never defaulted:

* **daily bars → `useRTH=True`.** ADR% and the SMA stack are RTH-only
  *structurally*, not by choice: both come off daily bars, and neither
  TradingView nor TC2000 permits anything else on a daily chart.
* **today's minutes → `useRTH=False`.** Session VWAP includes pre-market and
  anchors at 04:00 ET or first print, whichever is later. On a gapper that has
  done 2M shares before the open, **the pre-market VWAP is where the level sits
  at 09:31**, and an RTH-anchored one spends the first twenty minutes converging
  toward it — which is exactly the window the 1- and 5-minute playbooks trade.
"""
from __future__ import annotations

from typing import Optional, Sequence

from core.indicators.context import Bar
from .attach import Contract

#: A clientId that is NOT 11. 11 belongs to the capture, and reusing a live
#: client id is how two processes silently fight over one connection.
DEFAULT_CLIENT_ID = 22

#: `SPEC.md` §010 2 — 20-60 sessions of dailies. 60 gives the 50-day SMA room.
DAILY_DURATION = "60 D"

#: The RVOL curve wants 20 sessions of 1-minute bars. **IBKR's duration ceiling
#: for 1-minute bars is not 20 days on every account**, so this is requested and
#: allowed to refuse -- the refusal renders per row, which is the designed
#: behaviour rather than a fallback.
INTRADAY_DURATION = "20 D"


class IBKRMarketData:
    """Implements `live.attach.attach.MarketData` against a live TWS."""

    def __init__(self, ib, *, tick_slots_used: int = 0) -> None:
        self.ib = ib
        self._slots = tick_slots_used
        self._last_fetch: dict[str, float] = {}

    # ---- step 1 ---------------------------------------------------------

    def resolve(self, symbol: str) -> Sequence[Contract]:
        """**Never picks. Returns everything IBKR returned.**

        `attach()` refuses on more than one; that decision does not belong here,
        because a resolver that quietly returns its favourite makes the refusal
        unreachable and untestable.
        """
        from ib_async import Stock
        details = self.ib.reqContractDetails(Stock(symbol, "SMART", "USD"))
        out = []
        for d in details:
            c = d.contract
            out.append(Contract(symbol=c.symbol, con_id=c.conId,
                                exchange=c.exchange, currency=c.currency,
                                primary=c.primaryExchange or "",
                                sector_etf=_sector_etf(d)))
        return out

    # ---- step 2 ---------------------------------------------------------

    def tick_slots_in_use(self) -> int:
        return self._slots

    def cooldown_remaining_s(self, symbol: str) -> int:
        import time
        last = self._last_fetch.get(symbol.upper())
        if last is None:
            return 0
        from .attach import COOLDOWN_S
        remaining = COOLDOWN_S - (time.monotonic() - last)
        return max(0, int(round(remaining)))

    def _note_fetch(self, symbol: str) -> None:
        import time
        self._last_fetch[symbol.upper()] = time.monotonic()

    # ---- step 3: the three requests, and nothing else --------------------

    def daily_bars(self, c: Contract) -> Sequence[Bar]:
        self._note_fetch(c.symbol)
        return self._bars(c, DAILY_DURATION, "1 day", use_rth=True)

    def intraday_sessions(self, c: Contract) -> Sequence[Sequence[Bar]]:
        """20 sessions of 1-minute bars, split into sessions by date.

        **Split by the bar's own date, never by a fixed bar count** — a half
        day is a real session with fewer bars, and a fixed stride would smear
        two days together and silently shift the whole RVOL curve.
        """
        # use_rth=False, and this MATTERS -- it was wrong on the first live run.
        # `SPEC.md` 2f: **"RVOL must simply match itself -- today and the
        # 20-session reference on the same basis."** `today_minutes` is
        # use_rth=False because session VWAP includes pre-market, so a curve
        # built RTH-only puts the two sides of the ratio on different bases.
        #
        # The symptom was not a wrong number, which is the point: every RVOL
        # rendered `unavailable (no 20-session reference for 20:03)`, because
        # an RTH curve simply has no key past the close. **A basis mismatch
        # that refuses is the lucky version of this bug** -- the same mismatch
        # one minute earlier would have divided a pre-market-inclusive
        # numerator by an RTH-only denominator and rendered a plausible number.
        bars = self._bars(c, INTRADAY_DURATION, "1 min", use_rth=False)
        by_day: dict[str, list[Bar]] = {}
        for b in bars:
            by_day.setdefault(b.ts[:10], []).append(b)
        return [by_day[k] for k in sorted(by_day)]

    def today_minutes(self, c: Contract) -> Sequence[Bar]:
        # useRTH=False -- pre-market is IN. See the module docstring.
        return self._bars(c, "1 D", "1 min", use_rth=False)

    def sector_today_minutes(self, c: Contract) -> Optional[Sequence[Bar]]:
        if not c.sector_etf:
            return None
        return self.today_minutes(self._etf(c.sector_etf))

    def sector_sessions(self, c: Contract) -> Optional[Sequence[Sequence[Bar]]]:
        if not c.sector_etf:
            return None
        return self.intraday_sessions(self._etf(c.sector_etf))

    # ---- steps 4 and 5 ---------------------------------------------------

    def open_tick_stream(self, c: Contract) -> str:
        raise RuntimeError("tape not opened by S010 - no tape components in core")

    def playbook_for(self, c: Contract) -> str:
        return ""          # no playbook binding in this slice

    def year_high_low(self, c: Contract) -> tuple[Optional[float], Optional[float]]:
        bars = self._bars(c, "1 Y", "1 day", use_rth=True)
        if not bars:
            return (None, None)
        return (max(b.high for b in bars), min(b.low for b in bars))

    # ---- the one place a request is made --------------------------------

    def _bars(self, c: Contract, duration: str, size: str, *, use_rth: bool) -> list[Bar]:
        """**`use_rth` is keyword-only and has no default.** Omitting it is a
        TypeError rather than a silently RTH-only answer."""
        from ib_async import Stock
        contract = Stock(c.symbol, "SMART", c.currency)
        contract.conId = c.con_id
        raw = self.ib.reqHistoricalData(
            contract, endDateTime="", durationStr=duration,
            barSizeSetting=size, whatToShow="TRADES",
            useRTH=use_rth, formatDate=2)
        return [Bar(ts=str(b.date), open=b.open, high=b.high, low=b.low,
                    close=b.close, volume=float(b.volume),
                    wap=float(b.average) if b.average is not None else None)
                for b in raw]

    def _etf(self, symbol: str) -> Contract:
        return Contract(symbol=symbol, con_id=0, exchange="SMART")


def _sector_etf(details) -> Optional[str]:
    """Map IBKR's industry classification onto a sector ETF.

    **Returns `None` rather than a guess when nothing maps**, which is what
    makes `RVOL_rel` refuse by name instead of rendering `1.0`. An ETF has no
    industry of its own, so this correctly returns `None` for one.
    """
    industry = (getattr(details, "industry", "") or "").lower()
    category = (getattr(details, "category", "") or "").lower()
    text = f"{industry} {category}"
    for needle, etf in (("technolog", "XLK"), ("semiconduct", "XLK"),
                        ("financ", "XLF"), ("bank", "XLF"),
                        ("health", "XLV"), ("pharma", "XLV"),
                        ("energy", "XLE"), ("oil", "XLE"),
                        ("consumer, cyclical", "XLY"),
                        ("consumer, non-cyclical", "XLP"),
                        ("industrial", "XLI"), ("utilit", "XLU"),
                        ("basic materials", "XLB"),
                        ("communications", "XLC"), ("real estate", "XLRE")):
        if needle in text:
            return etf
    return None

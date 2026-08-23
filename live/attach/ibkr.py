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

**038 changed this and the change is the point.** The flag is no longer decided
here at all: **every request takes its `use_rth` from the `SessionBasis` constant
declared beside the indicator's own definition** in `core.indicators.context`.
There is no literal `use_rth=` anywhere in this module, and
`tests/test_session_basis.py` asserts the request actually issued carries the
constant's flag.

* **daily bars are requested ONCE PER DISTINCT BASIS.** `ADR%`, the SMA stack and
  `PDH`/`PDL` are RTH; **`ATR20` (`ATR14` before 065/B-091 moved the period) is
  ETH**, because the true range spans the prior close and the gap IS the
  measurement. Before 038 one RTH request served all four and `ATR14` read
  `13.14` against a true ~`15.6` — **-16 %, straight into the 3xATR stop floor
  and therefore into every share count.**
* **`SPEC.md:999` asserted that `useRTH` cannot alter a daily bar** — *"excluded,
  unchangeably — ETH cannot alter a daily bar."* **That is factually wrong and
  038 corrects it**; IBKR returns different daily highs, lows and volumes for the
  two flags, which is the whole reason any of this matters.
* **today's minutes → `useRTH=False`.** Session VWAP includes pre-market and
  anchors at 04:00 ET or first print, whichever is later. On a gapper that has
  done 2M shares before the open, **the pre-market VWAP is where the level sits
  at 09:31**, and an RTH-anchored one spends the first twenty minutes converging
  toward it — which is exactly the window the 1- and 5-minute playbooks trade.
"""
from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence
from zoneinfo import ZoneInfo

import yaml

from core.indicators.context import (ADR_BASIS, ATR_BASIS, Bar,
                                     INTRADAY_BASIS, SessionBasis)
from .attach import Contract

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "config" / "ibkr.yaml"

#: Session logic is US/Eastern via `zoneinfo`, never machine locale — the
#: workspace convention, applied at the one point raw broker time enters.
EASTERN = ZoneInfo("America/New_York")

#: The four settings, and there is no fifth. An unknown key is a REFUSAL rather
#: than a shrug: `clientId` where `client_id` was meant would otherwise be
#: accepted in silence while the real setting reported itself missing, and the
#: reader would be looking at a key that is right there in the file.
REQUIRED_SETTINGS = ("host", "port", "client_id",
                     "connect_timeout_s", "request_timeout_s")

#: **`DEFAULT_CLIENT_ID = 22` was deleted here, not moved** (034). It said *"a
#: clientId that is NOT 11"* and nothing read it — the id now comes from
#: `config/ibkr.yaml`, where §4.4 says settings live. A constant naming a second
#: client id, in the same module as the client that no longer uses it, is the
#: literal-in-two-places defect with the two copies already disagreeing.

#: `SPEC.md` §010 2 — 20-60 sessions of dailies. 60 gives the 50-day SMA room.
#: **058 Part 1: this now serves the ETH (ATR) fetch only.** The RTH fetch
#: moved to `LONG_DAILY_DURATION` below — see its docstring for why.
DAILY_DURATION = "60 D"

#: **058 Part 1.** ADR%, the SMA stack and PDH/PDL only ever read the TAIL of
#: whatever daily series they are given — `adr_pct`/`sma` slice `dailies[-n:]`
#: — so widening the RTH window from 60D to a full year changes none of their
#: answers. What it buys: 52wH/52wL/ATH (`LONG_BASIS`, ruled RTH by `041`)
#: read off the SAME series instead of issuing their own `1 Y` request, which
#: is exactly the redundant round trip `OBS-079` measured — two RTH daily
#: requests for the same contract, differing only in how far back they went.
#: Collapsing them takes the underlying's historical request count from five
#: to four, which is what puts the concurrent gather in `warm()` under IBKR's
#: six-per-two-seconds pacing limit **by construction**.
LONG_DAILY_DURATION = "1 Y"

#: The RVOL curve wants 20 sessions of 1-minute bars. **IBKR's duration ceiling
#: for 1-minute bars is not 20 days on every account**, so this is requested and
#: allowed to refuse -- the refusal renders per row, which is the designed
#: behaviour rather than a fallback.
INTRADAY_DURATION = "20 D"


@dataclass(frozen=True)
class IbkrConfig:
    """`config/ibkr.yaml`, loaded. **Every setting required, none defaulted.**

    `SPEC.md` §4.4. The class carries no field defaults on purpose: a default
    here would be a second place the value lives, and the file would stop being
    the answer to *what is this terminal connected to*.

    **The file PATH may default; the SETTINGS may not**, and the distinction is
    not a dodge. `live/tui/layout.py` draws the same line for `config/layout.yaml`
    — where the file lives is a fact about this repository's shape, whereas what
    is in it is a decision somebody made and has to be able to review.
    """

    host: str
    port: int
    client_id: int
    connect_timeout_s: int
    request_timeout_s: int
    #: setting name -> the `note` field that justified it. Loaded rather than
    #: discarded so `constraint:ibkr` is reachable from code and from a test,
    #: not only from a reader's eye passing over the file.
    notes: dict[str, str]

    @property
    def endpoint(self) -> str:
        """**Host and port together, and this is the string HEALTH renders.**

        034 part 3: a connection refusal must say *which host and port failed*.
        A refusal reading `could not connect` is indistinguishable between a
        stopped TWS, a paper port typed in place of a live one, and a Gateway
        that never came up — three different actions for one message.
        """
        return f"{self.host}:{self.port}"

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "IbkrConfig":
        p = path or CONFIG_PATH
        if not p.is_file():
            raise FileNotFoundError(
                f"{p} does not exist. The connection is configured, never "
                "defaulted (SPEC.md §4.4) — there is no built-in host, port or "
                "client id to fall back to, deliberately.")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        settings = data.get("settings")
        if not isinstance(settings, dict):
            raise ValueError(f"{p}: no `settings:` mapping.")

        missing = [k for k in REQUIRED_SETTINGS if k not in settings]
        if missing:
            raise ValueError(
                f"{p}: missing required settings {missing}. Every setting is "
                "required and none acquires a default.")
        unknown = sorted(set(settings) - set(REQUIRED_SETTINGS))
        if unknown:
            raise ValueError(
                f"{p}: unknown settings {unknown}. An unrecognised key is a "
                "typo that would otherwise be ignored in silence while the "
                "setting it was meant to be reported itself missing.")

        values: dict[str, Any] = {}
        notes: dict[str, str] = {}
        for key in REQUIRED_SETTINGS:
            entry = settings[key]
            if not isinstance(entry, dict) or "value" not in entry:
                raise ValueError(
                    f"{p}: `{key}` must be a mapping carrying `value` and "
                    f"`note`, got {entry!r}.")
            note = str(entry.get("note") or "").strip()
            if not note:
                # Structural, not advisory. A note that is merely conventional
                # is a note the next hurried change omits, and the reason a
                # setting has the value it has is exactly what nobody can
                # reconstruct later.
                raise ValueError(
                    f"{p}: `{key}` has no `note`. Every setting says why it is "
                    "what it is; a broker constraint says `constraint:ibkr`.")
            values[key], notes[key] = entry["value"], note

        for key in ("port", "client_id", "connect_timeout_s", "request_timeout_s"):
            v = values[key]
            # `isinstance(True, int)` is True in Python, and a bool here would
            # sail through as 0/1 — a client id of 1 nobody typed.
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"{p}: `{key}` must be an int, got {v!r}.")
        if not isinstance(values["host"], str) or not values["host"].strip():
            raise ValueError(f"{p}: `host` must be a non-empty string.")

        return cls(host=values["host"], port=values["port"],
                   client_id=values["client_id"],
                   connect_timeout_s=values["connect_timeout_s"],
                   request_timeout_s=values["request_timeout_s"],
                   notes=notes)


#: **058 Part 2.** IBKR's own documented limit: six or more historical
#: requests for the same Contract, Exchange and Tick Type inside two seconds
#: is a pacing violation — a rule separate from `attach.py`'s same-symbol
#: `COOLDOWN_S`. Five is the ceiling this guard enforces, one under the
#: violating count, so the sixth request is what trips it rather than the
#: request that would have been the violation itself.
PACING_WINDOW_S = 2.0
PACING_LIMIT = 5

#: `whatToShow="TRADES"` is the only tick type this module ever requests —
#: named here so the pacing key does not silently drift if that changes.
TICK_TYPE = "TRADES"


class _PacingGuard:
    """**Built, not assumed.** `OBS-079` found the six-per-two-seconds limit
    in IBKR's own docs, not in either sibling repo this project has, and
    058's instruction is explicit: *build the guard, do not rely on the
    arithmetic staying true.* A guard nobody has seen fail is `B-035` again.

    Tracks request timestamps per `(symbol, exchange, tick type)` and refuses
    a BATCH that would push that key's two-second window past `PACING_LIMIT`
    — refuses the whole attach rather than half-dispatching it, because a
    `gather()` that fires five of six requests and skips the sixth is a
    silent, uneven refusal nothing downstream could distinguish from a slow
    reply.
    """

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str, str], list[float]] = {}

    def check(self, key: tuple[str, str, str], count: int, *, now: float) -> None:
        if count == 0:
            return
        history = [t for t in self._seen.get(key, []) if now - t < PACING_WINDOW_S]
        if len(history) + count > PACING_LIMIT:
            raise RuntimeError(
                f"pacing limit - {len(history) + count} historical requests "
                f"for {key} within {PACING_WINDOW_S:.0f}s "
                f"(IBKR allows {PACING_LIMIT + 1}+ as a violation)")
        self._seen[key] = history + [now] * count


def _pacing_key(c: Contract) -> tuple[str, str, str]:
    return (c.symbol.upper(), c.exchange, TICK_TYPE)


def _contract_for(c: Contract):
    from ib_async import Stock
    contract = Stock(c.symbol, "SMART", c.currency)
    contract.conId = c.con_id
    return contract


def _request_kwargs(duration: str, size: str, *, use_rth: bool) -> dict:
    return dict(endDateTime="", durationStr=duration, barSizeSetting=size,
               whatToShow=TICK_TYPE, useRTH=use_rth, formatDate=2)


def _convert(raw) -> list[Bar]:
    return [Bar(ts=_eastern(b.date), open=b.open, high=b.high, low=b.low,
               close=b.close, volume=float(b.volume),
               wap=float(b.average) if b.average is not None else None)
           for b in raw]


class IBKRMarketData:
    """Implements `live.attach.attach.MarketData` against a live TWS."""

    def __init__(self, ib, *, tick_slots_used: int = 0) -> None:
        self.ib = ib
        self._slots = tick_slots_used
        self._last_fetch: dict[str, float] = {}
        #: **058 Part 2.** Populated by `warm()`, a concurrent gather of
        #: every independent historical request one attach needs. Keyed by
        #: ROLE (`"rth_dailies"`, `"eth_dailies"`, ...) rather than by the
        #: request shape (duration/useRTH) — a role's identity already fixes
        #: which window it was served, so there is no request the cache could
        #: be asked for that would need to disambiguate a narrower window
        #: from a wider cached one. `None` symbol = never warmed; the
        #: per-role methods below then fall back to their own single live
        #: request, exactly as before 058 — a fixture that never calls
        #: `warm()` is unaffected.
        self._warm: dict[str, Any] = {}
        self._warm_symbol: Optional[str] = None
        self._pacing = _PacingGuard()

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

    # ---- step 3: warm, then the per-role reads ----------------------------

    #: role name -> (contract-picker, duration, size, use_rth). One entry per
    #: independent request `warm()` gathers. **Declared once here rather than
    #: built inline** so `warm()`'s dispatch and its pacing check read off
    #: the same list and cannot silently diverge.
    #: **070, ruled by Christoph 2026-08-23: no ATR anywhere in ATTACHED.**
    #: The `eth_dailies` role (`ATR_BASIS`, `DAILY_DURATION`) is gone from
    #: this table — it fed only `_context_block`'s old ATR row, and that row
    #: no longer exists. `daily_bars(c, ATR_BASIS)` itself is unchanged and
    #: still correct for whoever calls it directly (TRADE's own task, when it
    #: needs ATR) — it simply falls through to a live, uncached fetch, the
    #: same as any role this table does not warm.
    _ROLES = (
        ("rth_dailies", "self", LONG_DAILY_DURATION, "1 day", ADR_BASIS.use_rth),
        ("today", "self", "1 D", "1 min", INTRADAY_BASIS.use_rth),
        ("sessions_raw", "self", INTRADAY_DURATION, "1 min", INTRADAY_BASIS.use_rth),
        ("sector_today", "etf", "1 D", "1 min", INTRADAY_BASIS.use_rth),
        ("sector_sessions_raw", "etf", INTRADAY_DURATION, "1 min", INTRADAY_BASIS.use_rth),
    )

    def warm(self, c: Contract) -> None:
        """**058 Part 2.** Every independent historical request this attach
        needs, gathered CONCURRENTLY via `asyncio.gather` on the existing
        `ibkr-broker` loop — not a second thread. `reqHistoricalDataMany`
        (below, on the transport) is the one seam that does that; this method
        just decides WHAT to ask for and stores what comes back.

        **Failure is per-role, never all-or-nothing.** Each entry in the
        result is either the converted bars or the exception that request
        raised — `_context_block`'s existing per-row refusal handling reads
        straight through this, because `daily_bars`/`today_minutes`/etc.
        below re-raise a cached exception exactly as a live call would have.

        Contract resolution (step 1) still gates this — `attach()` calls it
        only after a contract qualified — so the pacing guard's `check()` is
        the only thing standing between four-to-six requests and IBKR's
        actual limit, and it is checked BEFORE anything is dispatched.
        """
        self._note_fetch(c.symbol)
        etf = self._etf(c.sector_etf) if c.sector_etf else None
        roles = [r for r in self._ROLES if r[1] == "self" or etf is not None]
        contracts = {"self": c, "etf": etf}

        by_key: dict[tuple[str, str, str], int] = {}
        for _, which, *_r in roles:
            key = _pacing_key(contracts[which])
            by_key[key] = by_key.get(key, 0) + 1
        for key, count in by_key.items():
            self._pacing.check(key, count, now=time.monotonic())

        requests = [(_contract_for(contracts[which]),
                    _request_kwargs(duration, size, use_rth=use_rth))
                   for _, which, duration, size, use_rth in roles]
        outcomes = self.ib.reqHistoricalDataMany(requests)

        warm: dict[str, Any] = {}
        for (role, *_r), outcome in zip(roles, outcomes):
            warm[role] = outcome if isinstance(outcome, BaseException) else _convert(outcome)
        self._warm = warm
        self._warm_symbol = c.symbol.upper()

    def _warmed(self, c: Contract, role: str):
        """`None` = not warmed for this symbol/role — the caller falls back
        to its own live request. A cached EXCEPTION is re-raised rather than
        returned, so every caller's existing `try/except` handles a cache hit
        exactly like it handles a live failure."""
        if self._warm_symbol != c.symbol.upper() or role not in self._warm:
            return None
        outcome = self._warm[role]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def daily_bars(self, c: Contract, basis: SessionBasis) -> Sequence[Bar]:
        """**The caller passes the indicator's own basis constant.**

        Not a literal, and not a default. 038 Part 3: the value that reaches the
        request comes from the constant declared beside the definition, so a
        reader who wants to know which bars `ATR20` is built on reads `ATR_BASIS`
        and is done.

        **058 Part 1: the RTH duration is `LONG_DAILY_DURATION` (1 Y), not
        `DAILY_DURATION`.** ADR/the SMA stack/PDH-PDL only ever read the tail
        of what they are given, so the wider window changes none of their
        answers — and the same series is what `_context_block` now reads
        52wH/52wL off, with no second request.
        """
        role = "rth_dailies" if basis.use_rth else "eth_dailies"
        cached = self._warmed(c, role)
        if cached is not None:
            return cached
        self._note_fetch(c.symbol)
        duration = LONG_DAILY_DURATION if basis.use_rth else DAILY_DURATION
        return self._bars(c, duration, "1 day", use_rth=basis.use_rth)

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
        cached = self._warmed(c, "sessions_raw")
        bars = cached if cached is not None else self._bars(
            c, INTRADAY_DURATION, "1 min", use_rth=INTRADAY_BASIS.use_rth)
        by_day: dict[str, list[Bar]] = {}
        for b in bars:
            by_day.setdefault(b.ts[:10], []).append(b)
        return [by_day[k] for k in sorted(by_day)]

    def today_minutes(self, c: Contract) -> Sequence[Bar]:
        # Pre-market is IN, and the flag comes from INTRADAY_BASIS rather than
        # from a literal here. See the module docstring.
        cached = self._warmed(c, "today")
        if cached is not None:
            return cached
        return self._bars(c, "1 D", "1 min", use_rth=INTRADAY_BASIS.use_rth)

    def sector_today_minutes(self, c: Contract) -> Optional[Sequence[Bar]]:
        if not c.sector_etf:
            return None
        # **`_warmed(c, ...)` — the UNDERLYING contract, not the ETF.**
        # `warm()` keys its cache on the symbol it was called with, so a
        # sector role's cache hit is looked up against `c`, exactly as
        # `warm()` stored it — looking it up against the ETF would always
        # miss and silently fall through to a redundant live request.
        cached = self._warmed(c, "sector_today")
        if cached is not None:
            return cached
        return self.today_minutes(self._etf(c.sector_etf))

    def sector_sessions(self, c: Contract) -> Optional[Sequence[Sequence[Bar]]]:
        if not c.sector_etf:
            return None
        cached = self._warmed(c, "sector_sessions_raw")
        if cached is not None:
            by_day: dict[str, list[Bar]] = {}
            for b in cached:
                by_day.setdefault(b.ts[:10], []).append(b)
            return [by_day[k] for k in sorted(by_day)]
        return self.intraday_sessions(self._etf(c.sector_etf))

    # ---- steps 4 and 5 ---------------------------------------------------

    def open_tick_stream(self, c: Contract) -> str:
        raise RuntimeError("tape not opened by S010 - no tape components in core")

    def playbook_for(self, c: Contract) -> str:
        return ""          # no playbook binding in this slice

    # ---- the one place a SINGLE request is made ---------------------------

    def _bars(self, c: Contract, duration: str, size: str, *, use_rth: bool) -> list[Bar]:
        """**`use_rth` is keyword-only and has no default.** Omitting it is a
        TypeError rather than a silently RTH-only answer.

        **The fallback path only** — `warm()` (Part 2) is what a live attach
        actually goes through. This survives for any caller that reads a
        single role without warming first, which is every existing test of
        `daily_bars`/`today_minutes`/etc. in isolation."""
        raw = self.ib.reqHistoricalData(
            _contract_for(c), **_request_kwargs(duration, size, use_rth=use_rth))
        return _convert(raw)

    def _etf(self, symbol: str) -> Contract:
        return Contract(symbol=symbol, con_id=0, exchange="SMART")


def _eastern(raw) -> str:
    """**`formatDate=2` means UTC, and everything downstream reads Eastern.**

    Found on the first live attach and it is not a labelling problem. `Bar.ts` is
    a STRING that two separate consumers slice by position:

    * `attach.py` builds the pre-market and opening-range sets with
      `_clock(b.ts) < "09:30"` and `"09:30" <= _clock(b.ts) < "09:35"`. Against
      UTC stamps that selects **04:00–05:30 ET** as pre-market and
      **05:30–05:35 ET** as the opening range. The live run rendered
      `PMH · 90 pre-market bars` — ninety minutes, not the three hundred and
      thirty a 04:00 anchor gives — and an ORH/ORL taken four hours before the
      open. **Four rail values, all plausible, all wrong.**
    * `intraday_sessions` splits sessions on `b.ts[:10]`. Any bar after 20:00 ET
      carries the NEXT day in UTC, so an evening tail is filed as its own
      session and the 20-session RVOL reference silently shifts.

    Normalising at the seam fixes both, and the seam is the only place that can:
    `core` is timeframe-agnostic and correctly knows nothing about IBKR's wire
    format, so a fix there would be `core` learning about a broker.

    **Beyond 034's literal scope, and done anyway** — rendering a value known to
    be wrong is the thing this project exists to stop. Flagged in the done-note.

    Daily bars arrive as `date`, not `datetime`, and have no timezone to convert;
    they pass through as `YYYY-MM-DD`. `datetime` is a subclass of `date`, so the
    order of these checks is load-bearing.
    """
    if isinstance(raw, datetime):
        when = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return when.astimezone(EASTERN).strftime("%Y-%m-%d %H:%M:%S")
    return str(raw)


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


# ---- connecting, 034 -------------------------------------------------------
#
# **`ib_async`'s synchronous API cannot be called from inside Textual's event
# loop, and this was measured rather than assumed:**
#
#     RuntimeError: This event loop is already running
#
# `IB.connect()` and every `reqX()` are thin wrappers that call
# `loop.run_until_complete`, which is illegal re-entrantly. The TUI's attach runs
# inside `on_input_submitted`, which is a coroutine on Textual's loop, so the
# straightforward wiring raises on the first key press — and it raises in a place
# that looks like a broker fault rather than an architecture one.
#
# **Three ways out, and only one of them is in scope.** Making `MarketData`
# async would change the Protocol, `attach()`, and all 395 lines of
# `test_attach.py` — a redesign 034 does not ask for and explicitly leaves the
# attach binding unchanged. `util.patchAsyncio()` makes the loop re-entrant by
# monkeypatching asyncio itself, underneath a framework that owns the loop.
# **So the client gets its own loop on its own thread**, and the sync surface
# `IBKRMarketData` already expects is preserved by marshalling each call onto it.
#
# **The cost, stated because it is real and is a finding rather than a secret:
# the calling thread BLOCKS while a request runs, so an attach freezes the UI
# for the length of its historical requests.** `request_timeout_s` bounds it.
# Unfreezing it needed the attach moved to a Textual worker, which changes the
# binding 034 required unchanged — **done in 058**, see `live/tui/app.py` and
# its done-note. `warm()` below (058 Part 2) is the other half: it shrinks
# what the frozen window WAS, by dispatching the independent historical
# requests concurrently instead of one blocking round trip after another.


class _BrokerLoop:
    """A private asyncio loop on a daemon thread. **One per connection.**

    Daemon, so a terminal that is killed does not hang on a broker thread that
    is waiting on a socket. `close()` is still called on the normal path — a
    daemon thread is the backstop for the abnormal one, not the design.
    """

    def __init__(self, request_timeout_s: int) -> None:
        self._timeout = request_timeout_s
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="ibkr-broker",
                                        daemon=True)
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def call(self, make_awaitable, *, timeout: Optional[float] = None):
        """Run `make_awaitable()` **on the broker loop** and BLOCK for its answer.

        **A FACTORY, not an awaitable, and both halves of that were found the
        hard way against live TWS.**

        1. `ib_async`'s `reqXAsync` methods are not coroutine functions — they
           return an `asyncio.Future`. `run_coroutine_threadsafe` accepts only a
           coroutine and raises `TypeError` on a Future, which surfaced as
           `contract lookup failed (TypeError)` in the ATTACHED panel: a real
           refusal, correctly rendered, naming an exception class that says
           nothing about the actual fault.
        2. Even wrapped, calling `reqXAsync()` on the CALLER's thread builds
           that Future against the caller's loop — the wrong one. Passing a
           factory means the call itself happens inside the coroutine, on the
           broker loop, which is the only loop that will ever run it.

        **`timeout` is never `None` in effect.** An unbounded wait here is an
        unbounded freeze of the terminal, and a terminal that has stopped
        repainting is indistinguishable from one that has crashed.
        """
        async def _run():
            return await make_awaitable()

        future = asyncio.run_coroutine_threadsafe(_run(), self._loop)
        try:
            return future.result(timeout if timeout is not None else self._timeout)
        except TimeoutError:
            future.cancel()
            # The MESSAGE matters: `attach()`'s `_reason()` renders it verbatim
            # into the row that refused, and `TimeoutError` on its own tells a
            # reader nothing about which bound was hit.
            raise TimeoutError(
                f"no answer in {timeout or self._timeout}s "
                f"(request_timeout_s)") from None

    def call_many(self, factories, *, timeout: Optional[float] = None):
        """**058 Part 2.** Like `call()`, but N factories at once, via
        `asyncio.gather` on the SAME broker loop — one round trip instead of
        N. `return_exceptions=True` is the whole reason this is safe to use
        under Refusal A: one factory's exception comes back as a VALUE in the
        result list rather than aborting the others, so a caller reads
        through it exactly as it would a single `call()` that raised.
        """
        async def _run():
            return await asyncio.gather(
                *(make() for make in factories), return_exceptions=True)

        future = asyncio.run_coroutine_threadsafe(_run(), self._loop)
        try:
            return future.result(timeout if timeout is not None else self._timeout)
        except TimeoutError:
            future.cancel()
            raise TimeoutError(
                f"no answer in {timeout or self._timeout}s "
                f"(request_timeout_s)") from None

    def close(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


class _ThreadedIB:
    """The three calls `IBKRMarketData` makes, marshalled onto the broker loop.

    **Deliberately three methods and not a general proxy.** A `__getattr__`
    that forwarded anything would silently forward `placeOrder`, and the one
    property this connection must have is that it cannot place one. What is
    not written here cannot be reached through here.
    """

    def __init__(self, loop: _BrokerLoop, ib) -> None:
        self._loop, self._ib = loop, ib

    def reqContractDetails(self, contract):
        return self._loop.call(lambda: self._ib.reqContractDetailsAsync(contract))

    def reqHistoricalData(self, contract, **kwargs):
        return self._loop.call(
            lambda: self._ib.reqHistoricalDataAsync(contract, **kwargs))

    def reqHistoricalDataMany(self, requests):
        """**058 Part 2, the seam itself.** N `reqHistoricalDataAsync`
        coroutines, dispatched CONCURRENTLY via `asyncio.gather` on the
        existing `ibkr-broker` loop — not a second thread.
        `live/tests/test_attach_is_reachable_by_key.py::test_the_thread_bridge_carries_a_real_async_client`
        pins every call onto this one thread; `asyncio.gather` inside
        `call_many` satisfies that because it is concurrency WITHIN one loop,
        not a second loop running anywhere.
        """
        return self._loop.call_many(
            [lambda contract=contract, kw=kwargs:
             self._ib.reqHistoricalDataAsync(contract, **kw)
             for contract, kwargs in requests])


@dataclass
class BrokerConnection:
    """What `connect()` answers with. **A failure is a value, never a raise.**

    `SPEC.md` §4.2 — *surfaced, not refused*. The launcher must be able to put
    this straight onto the day record whether it worked or not, because a
    terminal that exits when TWS is down is a refusal nobody can read.
    """

    #: The name HEALTH renders. Carries host and port, always.
    source: str
    #: What to say about it — `connected · client 7`, or why not.
    state: str
    #: `None` when the connection failed. The app takes `md=None` already and
    #: renders a named refusal on attach, so there is nothing extra to handle.
    md: Optional[IBKRMarketData] = None
    _loop: Optional[_BrokerLoop] = None
    _ib: Optional[Any] = None

    @property
    def ok(self) -> bool:
        return self.md is not None

    def close(self) -> None:
        if self._ib is not None:
            try:
                self._ib.disconnect()
            except Exception:                          # noqa: BLE001
                pass                                   # shutting down anyway
        if self._loop is not None:
            self._loop.close()


def connect(cfg: IbkrConfig) -> BrokerConnection:
    """Dial TWS. **Never raises** — every failure comes back as a rendered state.

    **`readonly=True` is passed to `IB.connectAsync` and that is CODE, not
    convention.** The API session negotiates read-only with TWS, which then
    refuses order submission on this connection regardless of what any caller
    asks for. Only `tws_order` places orders; this is the enforcement in the
    tree rather than a rule in a file.
    """
    source = f"IBKR {cfg.endpoint}"
    loop = _BrokerLoop(cfg.request_timeout_s)
    try:
        from ib_async import IB
    except Exception as exc:                           # noqa: BLE001
        loop.close()
        return BrokerConnection(source=source,
                                state=f"not connected - ib_async unavailable ({exc})")

    # **058 Part 4.** `StartupFetch(0)` tells `ib_async` to skip its default
    # post-connect account/order/position sync — `ibkr_tape_tools`'
    # `test_conn.py:19-43` does exactly this. This connection is read-only
    # market data (`readonly=True` below) and never reads a position, an
    # order or an account balance, so that sync buys nothing here and costs
    # a second or two on every attach for free.
    #
    # **Feature-detected, not version-string-parsed, and not shimmed if
    # absent.** `OBS-079` found `StartupFetch` in `ibkr_tape_tools`'s use of
    # `ib_async`; this repo's own installed version (2.1.0, checked while
    # building 058) exposes it as `ib_async.ib.StartupFetch`. A future
    # downgrade or a machine without it still connects correctly — it just
    # pays for the sync it does not need, exactly as before this task.
    try:
        from ib_async.ib import StartupFetch
        fetch_nothing: dict[str, Any] = {"fetchFields": StartupFetch(0)}
    except ImportError:
        fetch_nothing = {}

    async def _make():
        # **`IB()` is constructed ON the broker loop.** It binds to whatever
        # loop is current at construction, so building it on the calling thread
        # would hand it the wrong one and every later request would target a
        # loop nobody is running.
        ib = IB()
        await ib.connectAsync(cfg.host, cfg.port, clientId=cfg.client_id,
                              timeout=cfg.connect_timeout_s, readonly=True,
                              **fetch_nothing)
        return ib

    try:
        # +5s so the wait outlives ib_async's own handshake timeout and the
        # error that surfaces is the broker's, not ours talking over it.
        ib = loop.call(_make, timeout=cfg.connect_timeout_s + 5)
    except Exception as exc:                           # noqa: BLE001
        loop.close()
        # **No `not connected -` prefix.** The row above carries the endpoint
        # and this one renders through `Cell.no_source`, which is already an
        # em-dash and a parenthesis — the grammar says *absent* without help.
        # The prefix cost 16 of the ~56 columns a HEALTH row has and pushed the
        # reason off the end, which is the only part that is not guessable.
        return BrokerConnection(source=source, state=_why(exc))

    return BrokerConnection(source=source,
                            state=f"connected · client {cfg.client_id} · read-only",
                            md=IBKRMarketData(_ThreadedIB(loop, ib)),
                            _loop=loop, _ib=ib)


#: The failure that actually happens, named in words rather than in the
#: operating system's. **This is a width decision as much as a wording one**:
#: Windows renders a refused connection as `[WinError 1225] The remote computer
#: refused the network connection`, 63 characters, which `fit` truncates off the
#: end of a HEALTH row — losing the reason and keeping the endpoint, when the
#: endpoint is the half a reader already knows.
_SHORT_REASON = {
    ConnectionRefusedError: "connection refused - nothing is listening",
    ConnectionResetError: "connection reset by the other end",
    TimeoutError: "timed out - listening, but no API answer",
}


def _why(exc: BaseException) -> str:
    """A reason a person can act on. **Not a traceback and not `error`** (034
    part 3).

    The two failures a reader must be able to tell apart are *nothing is
    listening* — TWS is not running, or the port is the other account's — and
    *something answered and then did not* — TWS is starting, or the API is
    switched off in its settings. Those need different actions, and the OS
    message for the first one is too long to survive the tile.
    """
    for kind, short in _SHORT_REASON.items():
        if isinstance(exc, kind):
            return short
    msg = " ".join(str(exc).split()).strip()
    return msg or type(exc).__name__


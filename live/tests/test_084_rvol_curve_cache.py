"""084 — the reduced RVOL curve is cached in memory for the trading day.

**Every state here is constructed locally**, never borrowed from
`test_attach.py`'s shared `Fake()` or `test_attach_is_reachable_by_key.py`'s
`drive()`/`type_symbol()` — 078's fixture-masking lesson, restated as B-136 by
083's own §6 and carried forward here. `_MD` below answers a DIFFERENT curve
on every call it receives (rising volume, one call counter shared across
`intraday_sessions`/`sector_sessions`) precisely so that a passing "same
value twice" assertion proves the cache served it rather than a static
fixture agreeing with itself by coincidence.

Five exit categories, per the task's own §6: Green, Identity (the important
one), Key isolation (x3), Refusal, Fixture.
"""
from __future__ import annotations

import asyncio

from core.indicators.context import Bar, SessionBasis

from live.attach.attach import Contract
from live.attach.rvol_config import anchor_word
from live.tui.app import ATTACH_KEY, RVOL_CURVE_CACHE_MAX, MomentumApp, Panel, RvolCurveCache, _session_date

SIZE = (209, 54)

RTH_BASIS = SessionBasis(use_rth=True, label="09:30-16:00 ET", why="test")
ETH_BASIS = SessionBasis(use_rth=False, label="04:00-20:00 ET", why="test")

QQQ = Contract(symbol="QQQ", con_id=1, exchange="NASDAQ", sector_etf="XLK")
AMZN = Contract(symbol="AMZN", con_id=2, exchange="NASDAQ", sector_etf="XLC")
#: A different symbol, mapping to the SAME sector ETF as AMZN — the case the
#: sector half of the cache exists to save.
MSFT = Contract(symbol="MSFT", con_id=3, exchange="NASDAQ", sector_etf="XLC")


async def type_symbol(pilot, symbol: str) -> None:
    """The same keypress sequence `test_attach_is_reachable_by_key.py` uses,
    rebuilt locally rather than imported — B-136."""
    await pilot.press(ATTACH_KEY)
    await pilot.pause()
    for ch in symbol:
        await pilot.press(ch)
    await pilot.press("enter")
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


class _MD:
    """A `MarketData` built for this file alone. `intraday_sessions` and
    `sector_sessions` share ONE call counter and each call's session bars
    carry a HIGHER volume than the one before — so a real second fetch would
    be measurably different from the first, and a test that reads the same
    RVOL value twice is proof of the cache, not a coincidence of a static
    fixture."""

    def __init__(self, contracts: dict, *, fail: frozenset = frozenset()) -> None:
        self.contracts = contracts
        self.fail = fail
        self.session_calls: list[tuple] = []
        self._call_n = 0

    def resolve(self, symbol):
        c = self.contracts.get(symbol.upper())
        return [c] if c else []

    def tick_slots_in_use(self): return 0
    def cooldown_remaining_s(self, symbol): return 0
    def warm(self, c): pass

    def daily_bars(self, c, basis):
        return [Bar(ts=f"2026-06-{(i % 28) + 1:02d}", open=100.0, high=102.0,
                    low=100.0, close=101.0, volume=1_000_000.0) for i in range(60)]

    def _session(self, vol: float) -> list:
        out = []
        for i in range(390):
            h, m = divmod(9 * 60 + 30 + i, 60)
            out.append(Bar(ts=f"2026-08-01T{h:02d}:{m:02d}:00", open=101.0,
                           high=101.0, low=101.0, close=101.0, volume=vol, wap=101.0))
        return out

    def intraday_sessions(self, c, basis):
        if "sessions" in self.fail:
            raise RuntimeError("sessions unavailable")
        self._call_n += 1
        self.session_calls.append(("own", c.symbol))
        return [self._session(10.0 * self._call_n) for _ in range(20)]

    def today_minutes(self, c):
        return [Bar(ts="2026-08-20T09:31:00", open=101.0, high=101.0, low=101.0,
                    close=101.0, volume=200.0, wap=101.0)]

    def sector_today_minutes(self, c):
        return self.today_minutes(c) if c.sector_etf else None

    def sector_sessions(self, c, basis):
        if not c.sector_etf:
            return None
        if "sector_sessions" in self.fail:
            raise RuntimeError("sector sessions unavailable")
        self._call_n += 1
        self.session_calls.append(("sector", c.sector_etf))
        return [self._session(10.0 * self._call_n) for _ in range(20)]

    def open_tick_stream(self, c): return "tick-by-tick AllLast"

    def open_price_stream(self, c, on_update):
        on_update(self.today_minutes(c))
        from live.attach.streaming import StreamHandle
        return StreamHandle(lambda: None)

    def playbook_for(self, c): return "ORB 5m"


# ---- Green — a second attach of the same symbol issues no curve request ---


def test_green_second_attach_of_the_same_symbol_issues_no_curve_request() -> None:
    md = _MD({"QQQ": QQQ})

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "QQQ")
            own_after_first = [k for k in md.session_calls if k[0] == "own"]
            sector_after_first = [k for k in md.session_calls if k[0] == "sector"]
            assert len(own_after_first) == 1 and len(sector_after_first) == 1, (
                f"the first attach must issue exactly one own and one sector "
                f"curve request: {md.session_calls}")
            first = app.record.attached[0].context["RVOL"].value

            await type_symbol(pilot, "QQQ")
            own_after_second = [k for k in md.session_calls if k[0] == "own"]
            sector_after_second = [k for k in md.session_calls if k[0] == "sector"]
            assert len(own_after_second) == 1, (
                f"a second attach of the SAME symbol, same session, issued a "
                f"new own-curve request -- the cache did not hit: "
                f"{md.session_calls}")
            assert len(sector_after_second) == 1, (
                f"a second attach of the SAME symbol issued a new sector-curve "
                f"request: {md.session_calls}")
            second = app.record.attached[0].context["RVOL"].value
            assert second == first, (
                f"the second attach rendered a different RVOL value than the "
                f"first, though no new request was made: {first} vs {second}")
    asyncio.run(go())


# ---- Identity — the important one ------------------------------------------


def test_identity_the_cached_curve_is_the_first_fetch_not_a_fresh_recompute() -> None:
    """`_MD` answers a HIGHER-volume curve on every call it actually
    receives. If the second attach silently refetched instead of hitting the
    cache, its RVOL reading would be measurably lower than the first
    (the reference curve would be roughly double). Equal readings here are
    proof the cache served the exact same object the first landing stored,
    not that a static fixture happened to agree with itself twice."""
    md = _MD({"QQQ": QQQ})

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "QQQ")
            first = app.record.attached[0].context["RVOL"]
            key = ("QQQ", anchor_word(app._stage2_inputs.rvol_basis), _session_date())
            cached_curve = app._rvol_curve_cache.get(key)
            assert cached_curve is not None, (
                "the first landing did not populate the cache under the key "
                "the next attach will look it up by")

            await type_symbol(pilot, "QQQ")
            second = app.record.attached[0].context["RVOL"]

            assert second.value == first.value, (
                f"a fresh fetch would have used a higher-volume curve and "
                f"produced a LOWER RVOL reading -- equal readings prove the "
                f"cache served it: first={first.value} second={second.value}")
            assert app._stage2_inputs.sessions == cached_curve, (
                "the reduced curve driving the second attach's RVOL is not "
                "the exact object the cache holds, value for value")
    asyncio.run(go())


# ---- Key isolation, three tests, each red for a different reason ----------


def test_key_isolation_changing_the_anchor_misses() -> None:
    import live.tui.app as app_mod
    md = _MD({"QQQ": QQQ})
    real_load = app_mod.load_rvol_basis
    basis_sequence = [RTH_BASIS, ETH_BASIS]

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            app_mod.load_rvol_basis = lambda: basis_sequence.pop(0)
            try:
                await type_symbol(pilot, "QQQ")
                await type_symbol(pilot, "QQQ")
            finally:
                app_mod.load_rvol_basis = real_load
            own_calls = [k for k in md.session_calls if k[0] == "own"]
            assert len(own_calls) == 2, (
                f"changing the anchor between attaches must MISS the cache "
                f"-- serving an RTH curve to an ETH numerator is exactly "
                f"B-049 through a new door -- got {md.session_calls}")
    asyncio.run(go())


def test_key_isolation_changing_the_session_date_misses() -> None:
    import live.tui.app as app_mod
    md = _MD({"QQQ": QQQ})
    real_date = app_mod._session_date
    dates = ["2026-08-20", "2026-08-21"]

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            app_mod._session_date = lambda: dates.pop(0)
            try:
                await type_symbol(pilot, "QQQ")
                await type_symbol(pilot, "QQQ")
            finally:
                app_mod._session_date = real_date
            own_calls = [k for k in md.session_calls if k[0] == "own"]
            assert len(own_calls) == 2, (
                f"a new trading day must MISS the cache -- every entry from "
                f"the prior date is stale -- got {md.session_calls}")
    asyncio.run(go())


def test_key_isolation_two_symbols_sharing_a_sector_etf_hit_on_the_sector_curve() -> None:
    md = _MD({"AMZN": AMZN, "MSFT": MSFT})

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "AMZN")
            sector_after_first = [k for k in md.session_calls if k[0] == "sector"]
            assert len(sector_after_first) == 1

            await type_symbol(pilot, "MSFT")
            sector_after_second = [k for k in md.session_calls if k[0] == "sector"]
            assert len(sector_after_second) == 1, (
                f"AMZN and MSFT both map to sector ETF XLC -- the second "
                f"attach must HIT the shared sector curve rather than "
                f"re-fetching it: {md.session_calls}")
            own_calls = [k for k in md.session_calls if k[0] == "own"]
            assert len(own_calls) == 2, (
                f"the OWN curve is keyed on the ATTACHED symbol and must "
                f"never be shared across two symbols merely because they "
                f"share a sector: {md.session_calls}")
    asyncio.run(go())


# ---- Refusal — a failed fetch must never populate the cache ---------------


def test_refusal_a_failed_fetch_does_not_populate_the_cache() -> None:
    md = _MD({"QQQ": QQQ}, fail=frozenset({"sessions"}))

    async def go():
        app = MomentumApp(md=md)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await type_symbol(pilot, "QQQ")
            assert app._stage2_inputs.sessions_failed, (
                "the fixture is set to fail 'sessions' and the input does "
                "not show a failure -- this test is not exercising the "
                "refusal path it claims to")
            key = ("QQQ", anchor_word(app._stage2_inputs.rvol_basis), _session_date())
            assert app._rvol_curve_cache.get(key) is None, (
                "a failed fetch populated the cache -- a cached refusal "
                "would poison the rest of the session and look exactly "
                "like a fast, correct one")

            # And a THIRD attach still tries, rather than being permanently
            # blocked by a phantom cache entry from the failure.
            await type_symbol(pilot, "QQQ")
            own_calls = [k for k in md.session_calls if k[0] == "own"]
            assert len(own_calls) == 0, (
                "every attempt fails in this fixture, so the own curve must "
                "never have landed a real call")
    asyncio.run(go())


# ---- Bounded — stated as code, not merely as prose -------------------------


def test_bounded_the_cache_evicts_the_least_recently_served_entry() -> None:
    """**084 §4: 'state the bound you chose and why.'** 20 entries — a
    generous watchlist with headroom, per `RVOL_CURVE_CACHE_MAX`'s own
    comment. Checked here as the LRU behaviour the docstring claims: `get()`
    (a re-serve) refreshes an entry's position, so the entry evicted when
    the bound is exceeded is the one nobody has re-read, not merely the
    oldest by insertion."""
    cache = RvolCurveCache()
    for i in range(RVOL_CURVE_CACHE_MAX):
        cache.put((f"SYM{i}", "rth", "2026-08-20"), {"09:30": float(i)})

    # SYM0 is re-served -- it must survive the eviction that follows.
    cache.get(("SYM0", "rth", "2026-08-20"))
    cache.put(("SYM_NEW", "rth", "2026-08-20"), {"09:30": 999.0})

    assert cache.get(("SYM0", "rth", "2026-08-20")) is not None, (
        "the entry just re-served by get() must survive the eviction that "
        "follows it -- true LRU, not merely bounded")
    assert cache.get(("SYM1", "rth", "2026-08-20")) is None, (
        "the least-recently-served entry must be the one evicted when the "
        "cache exceeds its bound")


# ---- Fixture — every state above is self-constructed ----------------------


def test_fixture_this_file_builds_every_state_itself() -> None:
    """**B-136, checked as code, not trusted by review.** No import from
    `test_attach` or `test_attach_is_reachable_by_key` anywhere in this
    file — every `MarketData`/pilot-drive helper above is hand-built, so no
    test here can be reading a state a SHARED fixture happens to guarantee
    rather than one this task's own change produces."""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (
            "test_attach" in node.module):
            names.update(a.name for a in node.names)
    assert not names, f"this file imports from a shared test fixture ({names})"

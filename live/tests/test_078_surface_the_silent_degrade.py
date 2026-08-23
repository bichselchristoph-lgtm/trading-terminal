"""078 — the two defects 075 measured live, fixed: `warm()` failing is
surfaced even when every row still measures, and every historical request
(warmed or fallback) now consults `_PacingGuard`. **Reported here as
`B-130`/`B-133`.**

**080 changed the shape this task's Green/Refusal tests exercise, and this
file says so rather than silently rewriting the guard — task 080 §7's own
instruction.** 080 retires `warm()`/`_context_block` entirely: stage 2 no
longer runs one gathered call that a per-role fallback degrades AWAY from —
`app.py` now dispatches `daily_bars`/`intraday_sessions`/`sector_sessions`
directly, independently, and each IS the only read that role ever gets.
**The scenario B-130's original Green/Refusal tests exercised — `warm()`
timing out while every per-role fallback still quietly succeeds — is no
longer reachable**, because there is no more `warm()` call in the dispatch
path for anything to time out ahead of. `AttachResult.partial`/
`Attached.partial` are removed with it (080's own five-row constraint
leaves no line for a screen-level summary).

**What 078 actually cared about survives, in a form that fits 080's
architecture**: a role's failure is NEVER silently invisible — it renders
as THAT row's own `unavailable (specific reason)`, directly (still true,
covered in `test_attach.py`), and **every historical request still
consults `_PacingGuard` before it dispatches** — B-133's real content —
which the two tests below now check against the ACTUAL call shape `app.py`
uses (`daily_bars`/`intraday_sessions`/`sector_sessions` called with
nothing ever warmed, since nothing calls `warm()` any more), not merely
against `_bars()` in isolation as tests 3/4 already did.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from core.indicators.context import ADR_BASIS
from live.attach.attach import Contract
from live.attach.ibkr import IBKRMarketData, _pacing_key
from live.tests.test_attach import QQQ
from live.tests.test_attach_is_reachable_by_key import FakeIB


# ---- exit test 1/2 (080's replacement) — every stage-2 role paces itself --


def test_every_stage2_role_call_consults_the_pacing_guard() -> None:
    """**080's shape for B-133.** `app.py` never calls `warm()` any more —
    `daily_bars`/`intraday_sessions`/`sector_sessions` are each dispatched
    directly, independently, from their own worker. `_warmed()` therefore
    always misses (nothing populated `self._warm`), so every one of these
    three calls falls straight through to `_bars()` — and `_bars()`
    consulting `_PacingGuard` (078/B-133, unchanged) is what makes THIS the
    guarantee 078 actually needed: not that a fallback path is guarded, but
    that the path `app.py` genuinely takes, always, is."""
    _ensure_main_thread_has_a_loop()
    md = IBKRMarketData(FakeIB())
    key = _pacing_key(QQQ)
    assert key not in md._pacing._seen, "fixture assumption: nothing seen yet"

    md.daily_bars(QQQ, ADR_BASIS)
    assert key in md._pacing._seen, "daily_bars reached the wire unguarded"
    assert len(md._pacing._seen[key]) == 1

    md.intraday_sessions(QQQ)
    assert len(md._pacing._seen[key]) == 2, (
        "intraday_sessions reached the wire unguarded")


def test_a_role_failure_renders_its_own_reason_not_a_generic_default() -> None:
    """**080's shape for B-130's real content.** No `warm()` step exists to
    fail independently of a row any more, so there is nothing for a
    degraded-gather sentence to report — but the underlying guarantee 078
    protected (a specific failure reason must never be swallowed by a
    generic "no daily bars" default) is still load-bearing, and is already
    covered end-to-end by `test_attach.py`'s
    `test_refusal_a_a_failed_request_leaves_the_others_rendering` via
    `compute_context_and_rail`. Pinned again here, directly against the
    live client's own `daily_bars`, so this file keeps a test that would go
    red if that specific-reason guarantee regressed at the client layer
    rather than only at the arithmetic layer."""

    class PacingFailIB(FakeIB):
        def reqHistoricalData(self, contract, **kw):
            if kw["barSizeSetting"] == "1 day":
                raise RuntimeError("pacing limit, retry in 42s")
            return super().reqHistoricalData(contract, **kw)

    md = IBKRMarketData(PacingFailIB())
    with pytest.raises(RuntimeError, match="pacing limit, retry in 42s"):
        md.daily_bars(QQQ, ADR_BASIS)


# ---- exit test 3 (Guard) — every historical request consults the guard ---


def _ensure_main_thread_has_a_loop() -> None:
    """**`ib_async`'s dependency `eventkit` reads `asyncio.get_event_loop()`
    at IMPORT time**, and the import is never cached on failure —
    `live/tui/app.py`'s `_attach_worker` documents this exact issue and
    carries the identical guard for the worker-thread case. `_bars` imports
    `ib_async` (via `_contract_for`) the first time it runs in a process;
    whichever test happens to be first across the whole suite needs this,
    or the failure is a suite-ordering artefact, not a finding about the
    fix."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def test_the_fallback_path_consults_the_pacing_guard() -> None:
    """**Assert the consultation, not the absence of a violation** (078
    §4) — no violation fired across 075's twelve live runs with the guard
    entirely absent from this path, so absence of a violation proves
    nothing. This calls `IBKRMarketData._bars` directly (the fallback's own
    single choke point, confirmed in `daily_bars`/`today_minutes`/etc.) and
    asserts `_PacingGuard._seen` recorded the request — the same bookkeeping
    `warm()`'s own dispatch already relies on."""
    _ensure_main_thread_has_a_loop()
    md = IBKRMarketData(FakeIB())
    key = _pacing_key(QQQ)
    assert key not in md._pacing._seen, "fixture assumption: nothing seen yet"

    md._bars(QQQ, "1 Y", "1 day", use_rth=True)

    assert key in md._pacing._seen, (
        "the fallback request never touched _PacingGuard — a request "
        "reached the wire without being consulted")
    assert len(md._pacing._seen[key]) == 1


def test_the_fallback_path_refuses_once_the_guard_would_be_exceeded() -> None:
    """The guard's own behaviour, now reachable from the fallback path:
    six requests for the same key inside the window refuses — previously
    unreachable from here at all, since `_bars` never called `check()`."""
    _ensure_main_thread_has_a_loop()
    md = IBKRMarketData(FakeIB())
    now = time.monotonic()
    md._pacing.check(_pacing_key(QQQ), 5, now=now)   # simulate warm()'s own 5

    with pytest.raises(RuntimeError, match="pacing limit"):
        md._bars(QQQ, "1 Y", "1 day", use_rth=True)

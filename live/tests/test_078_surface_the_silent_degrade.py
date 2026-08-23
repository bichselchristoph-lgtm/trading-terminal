"""078 — the two defects 075 measured live, fixed: `warm()` failing is
surfaced even when every row still measures, and every historical request
(warmed or fallback) now consults `_PacingGuard`.

**075's own finding, restated**: on 3 of 6 AMZN attaches `warm()` timed out,
every per-role read fell back to its own unguarded live request, every one
of those fallbacks succeeded, and nothing anywhere said the fast path had
failed. `_bars` — the single choke point every fallback goes through — never
consulted `_PacingGuard`. Both reported here as `B-130`/`B-133`.

**Reuses existing vocabulary, per 078 §3**: no new grammar token, no new
colour, no new row — `AttachResult.partial`/`Attached.partial` is the same
field `058` built for "the gather completed with some rows refusing";
`context_rows()`'s rendering of it (`{partial} (flagged, not an error)`) is
untouched. Only a new SENTENCE for a cause that previously had none at all.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from live.attach.attach import Contract, attach
from live.attach.ibkr import IBKRMarketData, _pacing_key
from live.tests.test_attach import QQQ, Fake, minutes
from live.tests.test_attach_is_reachable_by_key import FakeIB
from live.tui.app import MomentumApp, context_rows
from live.tui.day_record import Attached


class FakeWithPremarket(Fake):
    """`Fake.today_minutes` always starts at 09:30 — no fixture in
    `test_attach.py` ever gives PMH/PML a pre-market bar, so `refused` is
    never actually empty against the shared `Fake`. This fixture starts at
    08:00 (120 bars → 08:00 through 09:59) so a genuinely CLEAN attach —
    every row `ok`, including PMH/PML — is reachable for the GREEN test,
    which needs `refused` to be empty so the degraded-gather sentence is
    not masked by an unrelated ordinary refusal."""

    def today_minutes(self, c):
        self._maybe("today")
        return minutes(120, start_h=8, start_m=0)


# ---- exit test 1 (Green) — warm() fails, every row still measures --------


def test_a_failed_warm_that_still_measures_reports_a_degraded_gather() -> None:
    """`FakeWithPremarket(fail=["warm"])`: `warm()` raises; every per-role
    method is still its own, independent, always-succeeding read (`Fake`
    never checks a warm cache), so every row lands `ok` — `refused` stays
    empty and, pre-078, `AttachResult.partial` stayed `""`: a fully
    successful-looking attach that had actually taken the slow, unguarded
    path throughout. **Exact wording asserted, not a substring** (078 §4 /
    B-126)."""
    r = attach("QQQ", FakeWithPremarket(fail=["warm"]))
    assert r.attached
    values = {**r.context, **r.rail}
    assert all(v.ok for v in values.values()), (
        "fixture assumption broken: every row must measure for this to be "
        "the GREEN case, not the REFUSAL case")
    assert r.partial == "gather degraded - warm unavailable", (
        f"expected the exact degraded-gather sentence, got {r.partial!r}")

    # And on the rendered panel — same field, same row, same suffix.
    a = Attached(symbol=r.symbol, since="09:31:00", context=r.context,
                rail=r.rail, partial=r.partial)
    body = "\n".join(context_rows(a))
    assert "gather degraded - warm unavailable (flagged, not an error)" in body, (
        f"the degraded-gather line did not render:\n{body}")


def test_a_clean_warm_reports_no_partial_at_all() -> None:
    """The control: `warm()` succeeding, with no other row refusing, must
    NOT produce any `partial` — otherwise the degraded-gather sentence
    would be meaningless noise on every attach rather than a signal on a
    real one."""
    r = attach("QQQ", FakeWithPremarket())
    assert r.attached and not r.partial


# ---- exit test 2 (Refusal) — warm() fails AND a fallback also fails ------


def test_warm_and_fallback_both_failing_refuses_with_a_specific_reason() -> None:
    """`Fake(fail=["warm", "daily"])`. The affected rows (everything reading
    `daily_bars` — `ADR% used`, `ext 10/20/50`, `PDH`/`PDL`, `52wH`/`52wL`)
    must refuse with the SPECIFIC reason their shared fallback raised — not
    the generic `"no daily bars"` default a successful-but-empty read would
    carry. **That distinction is the assertion**: a reason-carrying refusal
    must not be confusable with "the read succeeded and simply returned
    nothing." `refused` is non-empty here (both the daily-dependent rows
    AND the base fixture's own PMH/PML gap), so this also exercises the
    COMBINED message — a real refusal never silently swallows the
    degraded-gather fact, and vice versa."""
    r = attach("QQQ", Fake(fail=["warm", "daily"]))
    assert r.attached
    adr = r.context["ADR% used"]
    assert not adr.ok
    assert adr.unavailable == "pacing limit, retry in 42s", (
        f"expected the fallback's own specific exception reason, got "
        f"{adr.unavailable!r} — a generic default here would be "
        f"indistinguishable from 'the read succeeded and returned nothing'")
    assert adr.unavailable != "no daily bars", (
        "the specific failure reason was overwritten by the generic "
        "empty-read default — the two must stay distinguishable")

    # Both facts are true here (rows refused AND warm() itself failed), so
    # the screen-level statement carries both — neither silently swallows
    # the other.
    values = {**r.context, **r.rail}
    refused = [k for k, v in values.items() if not v.ok]
    assert refused, "fixture assumption: at least one row must refuse here"
    assert r.partial == (f"{len(refused)} of {len(values)} rows unavailable "
                         f"(gather degraded - warm unavailable)"), (
        f"unexpected partial: {r.partial!r}")


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

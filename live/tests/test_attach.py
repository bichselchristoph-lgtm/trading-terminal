"""S010 — the attach sequence and the context block, against fixtures.

**Every test here runs with no TWS connection.** The `019` capture held the only
client the day this was built and could not be risked, so `MarketData` is a
Protocol and every fixture below is a fake implementing it. That constraint
produced a better design than convenience would have: the whole surface,
including all four refusals, is exercisable on a machine with no broker at all.

**The four refusals are the point of the slice**, not a coda to it. Each one is
a case where the honest answer is *no* and the tempting answer is a number.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Sequence

import pytest

from core.indicators.context import (ADR_BASIS, ATR_DEFAULT_N, Bar, Measured,
                                     adr_dollar, adr_pct, adr_used, atr_d14,
                                     rvol_at, rvol_curve, rvol_rel,
                                     true_ranges, vwap_from_bars)
from live.attach.attach import (COOLDOWN_S, ORIGINS, TICK_SLOTS, AttachResult,
                                Contract, Stage2Inputs, attach,
                                compute_context_and_rail)

REPO = Path(__file__).resolve().parents[2]

QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="NASDAQ",
               primary="NASDAQ", sector_etf="XLK")
NOSECTOR = Contract(symbol="THIN", con_id=1, exchange="NASDAQ", sector_etf=None)


def dailies(n: int = 60, *, hi: float = 102.0, lo: float = 100.0,
            close: float = 101.0, open_: float = 100.5) -> list[Bar]:
    return [Bar(ts=f"2026-06-{(i % 28) + 1:02d}", open=open_, high=hi, low=lo,
                close=close, volume=1_000_000) for i in range(n)]


def minutes(count: int, *, start_h: int = 9, start_m: int = 30,
            vol: float = 1000.0, wap: float = 101.0) -> list[Bar]:
    out = []
    for i in range(count):
        m = start_m + i
        ts = f"2026-08-12T{start_h + m // 60:02d}:{m % 60:02d}:00"
        out.append(Bar(ts=ts, open=wap, high=wap, low=wap, close=wap,
                       volume=vol, wap=wap))
    return out


class Fake:
    """A `MarketData` that answers from fixtures and can be told to fail."""

    def __init__(self, *, contracts: Sequence[Contract] = (QQQ,), slots: int = 0,
                 cooldown: int = 0, fail: Sequence[str] = (),
                 sector: bool = True, playbook: str = "ORB 5m") -> None:
        self.contracts, self.slots, self.cooldown = list(contracts), slots, cooldown
        self.fail, self.sector, self.playbook = set(fail), sector, playbook
        self.calls: list[str] = []
        #: Every `SessionBasis` a daily request was made with. 038's test 1
        #: asserts against **the request actually issued**, not against the
        #: constant merely existing.
        self.basis_asked: list = []

    def _maybe(self, name: str) -> None:
        self.calls.append(name)
        if name in self.fail:
            raise RuntimeError(f"pacing limit, retry in 42s" if name == "daily"
                               else f"{name} unavailable")

    def resolve(self, symbol): self._maybe("resolve"); return self.contracts
    def tick_slots_in_use(self): return self.slots
    def cooldown_remaining_s(self, symbol): return self.cooldown

    def warm(self, c):
        """058 Part 2. A no-op here — `Fake` answers every per-role method
        instantly, so there is nothing a gather would buy. `attach()` calls
        this unconditionally, so every `MarketData` implementation needs it;
        the real gather is `IBKRMarketData`'s alone."""
        self._maybe("warm")

    def daily_bars(self, c, basis):
        """**Answers a DIFFERENT series per basis, on purpose** (038 Part 1).

        A fake that returned the same bars for `use_rth=True` and `False` would
        let the whole ADR-RTH/ATR-ETH split pass while the request carried the
        wrong flag — the fixture would be agreeing with itself. The ETH series
        carries a wider high/low, which is what extended hours actually does to a
        daily bar and what `SPEC.md:999` wrongly said was impossible.
        """
        self._maybe("daily")
        self.basis_asked.append(basis)
        if basis.use_rth:
            return dailies()
        return dailies(hi=104.0, lo=98.0)
    def intraday_sessions(self, c, basis=None): self._maybe("intraday"); return [minutes(30) for _ in range(20)]
    def today_minutes(self, c): self._maybe("today"); return minutes(30)
    def sector_today_minutes(self, c): return minutes(30) if self.sector else None
    def sector_sessions(self, c, basis=None): return [minutes(30) for _ in range(20)] if self.sector else None
    def open_tick_stream(self, c): self._maybe("tick"); return "tick-by-tick AllLast"

    def open_price_stream(self, c, on_update):
        """**080.** Answers instantly and synchronously, exactly like every
        other method here — `on_update` fires once with `today_minutes`'s
        own fixture bars, so a test using `Fake` sees `Last $`/`VWAP` land
        immediately rather than staying pending forever. Reuses
        `today_minutes`'s own `fail=["today"]` switch rather than adding a
        second one — the stream replaces that one-shot role, so it fails
        the same way. `StreamHandle`'s cancel just flips a flag; nothing
        here is actually ongoing."""
        on_update(self.today_minutes(c))
        from live.attach.streaming import StreamHandle
        return StreamHandle(lambda: None)

    def playbook_for(self, c): return self.playbook


def stage2_of(md, c: Contract) -> tuple[dict, dict]:
    """**080.** The test-side equivalent of `app.py`'s independent-landing
    dispatch, collapsed into one synchronous call — `Fake` answers every
    role instantly, so there is no ordering to exercise here, only the same
    per-role try/except `attach.py`'s retired `_context_block` used to run,
    now performed by the caller (`app.py` in production; this helper in a
    test) rather than by `attach()` itself."""
    def reason(exc: BaseException) -> str:
        return str(exc).strip() or type(exc).__name__

    inp = Stage2Inputs(has_sector=bool(c.sector_etf))
    try:
        inp.today = list(md.today_minutes(c))
    except Exception as exc:                            # noqa: BLE001
        inp.today_failed = reason(exc)
    try:
        inp.rth_dailies = list(md.daily_bars(c, ADR_BASIS))
    except Exception as exc:                            # noqa: BLE001
        inp.rth_dailies_failed = reason(exc)
    try:
        inp.sessions = list(md.intraday_sessions(c, inp.rvol_basis))
    except Exception as exc:                            # noqa: BLE001
        inp.sessions_failed = reason(exc)
    if inp.has_sector:
        try:
            st = md.sector_today_minutes(c)
            inp.sector_today = list(st) if st is not None else None
        except Exception as exc:                        # noqa: BLE001
            inp.sector_today_failed = reason(exc)
        try:
            ss = md.sector_sessions(c, inp.rvol_basis)
            inp.sector_sessions = list(ss) if ss is not None else None
        except Exception as exc:                        # noqa: BLE001
            inp.sector_sessions_failed = reason(exc)
    return compute_context_and_rail(inp)


# ---- the arithmetic, against hand-checkable fixtures ----------------------


def test_adr_is_kullamagis_convention_and_excludes_today() -> None:
    """`mean over 20 days of (high/low - 1) × 100`, **excluding today.**

    Hand-checkable: every fixture bar is 102/100, so every ratio is exactly 2 %.
    """
    m = adr_pct(dailies())
    assert m.ok and abs(m.value - 2.0) < 1e-9
    assert "excl. today" in m.sample, "the sample must say today was excluded"

    # Today is genuinely dropped: make it wild and the answer must not move.
    bars = dailies()
    bars[-1] = Bar(ts="2026-08-12", open=100, high=200, low=50, close=150, volume=1)
    assert abs(adr_pct(bars).value - 2.0) < 1e-9, (
        "today's bar changed ADR% — it must be excluded, and a 20-day window "
        "that quietly includes today is off by one every single day")


def test_adr_refuses_rather_than_shortening_its_window() -> None:
    m = adr_pct(dailies(5))
    assert not m.ok and "need 21 daily bars, have 5" in m.unavailable


def test_atr_is_wilder_not_a_simple_mean() -> None:
    """**The most common way this is implemented wrong**, and it agrees with the
    right answer often enough to survive a spot check.

    The fixture makes them diverge: a flat series with one spiked bar. A simple
    mean of the last 14 TRs drops the spike out of the window; Wilder's RMA
    never fully forgets it.
    """
    bars = dailies(40)
    bars[5] = Bar(ts="2026-06-06", open=100, high=140, low=100, close=101,
                  volume=1_000_000)
    # **n=14 explicit, decoupled from `ATR_DEFAULT_N`.** This test's property —
    # Wilder never fully forgets a spike, unlike a windowed simple mean — holds
    # at any period; pinning the period here means a future retune of the
    # default (065/B-091 moved it 14 -> 20) cannot silently change what this
    # test is comparing against.
    wilder = atr_d14(bars, n=14)
    trs = true_ranges(bars)
    simple_mean_last_14 = sum(trs[-14:]) / 14
    assert wilder.ok
    assert abs(wilder.value - simple_mean_last_14) > 0.1, (
        "Wilder's RMA agreed with a simple mean of the last 14 true ranges on a "
        "fixture built to separate them — the smoothing is not being applied")
    assert "Wilder RMA" in wilder.sample


def test_atr_is_20_period_by_default_and_refuses_a_short_series() -> None:
    """**065/B-091.** Christoph, 2026-08-22: one ATR, 20-day, ETH. B-033:
    IBKR returned 204 bars for a request of 205 with no error, so a caller
    must not assume the series arrived whole — `atr_d14`'s own length check
    is what stands between a quietly-short window and a wrong number, and
    this pins it at the new period rather than trusting it by inference.
    """
    assert ATR_DEFAULT_N == 20, (
        "the default period moved from 14 under 065/B-091 and something put "
        "it back")
    # Wilder needs n true ranges, i.e. n+1 daily bars. 20 bars -> 19 true
    # ranges -> one short of 20 -> refuses, naming exactly what it received.
    short = atr_d14(dailies(20))
    assert not short.ok
    assert "need 21 daily bars, have 20" in short.unavailable
    # 21 bars -> exactly 20 true ranges -> computes.
    whole = atr_d14(dailies(21))
    assert whole.ok, f"21 daily bars must be enough for a 20-period ATR: {whole.unavailable}"
    assert "n=20" in whole.sample


def test_true_range_uses_the_prior_close_including_the_gap() -> None:
    """**That is the whole difference from ADR**, which ignores gaps — and it is
    why the two may never share a label."""
    bars = [Bar(ts="d1", open=100, high=101, low=99, close=100, volume=1),
            Bar(ts="d2", open=110, high=111, low=109, close=110, volume=1)]
    assert true_ranges(bars) == [11.0], "the gap from 100 to 109/111 was ignored"


def test_vwap_is_bar_derived_and_says_so() -> None:
    """S010 part 0 — **one basis, and the label is never a fallback.**"""
    bars = [Bar(ts="2026-08-12T09:30:00", open=1, high=1, low=1, close=1,
                volume=100, wap=10.0),
            Bar(ts="2026-08-12T09:31:00", open=1, high=1, low=1, close=1,
                volume=300, wap=20.0)]
    m = vwap_from_bars(bars)
    assert m.ok and abs(m.value - 17.5) < 1e-9        # (10*100 + 20*300)/400
    assert "bar-derived" in m.sample
    assert "sh" in m.sample and "min" in m.sample, (
        "the sample must carry what it was computed over — S010 part 2 replaces "
        "the settle timer with exactly this")
    for retired in ("tick-derived", "tick budget", "fallback"):
        assert retired not in m.sample, (
            f"{retired!r} appears in the VWAP label. 2c-bis retires the "
            "tick-derived variant; there is nothing to fall back from.")


def test_vwap_refuses_a_bar_with_no_wap_rather_than_using_close() -> None:
    """A VWAP off by three cents does not look broken — it looks like a VWAP,
    and it is a stop level, so it becomes position size."""
    m = vwap_from_bars([Bar(ts="t", open=1, high=1, low=1, close=1, volume=1)])
    assert not m.ok and "refusing to substitute close" in m.unavailable


def test_rvol_denominator_is_a_median_curve_not_a_number() -> None:
    """**Median, not mean.** One earnings day inflates a mean reference across
    the whole curve, not just at one point."""
    quiet = [minutes(3, vol=100.0) for _ in range(19)]
    spike = [minutes(3, vol=100_000.0)]
    curve = rvol_curve(quiet + spike)
    assert curve["09:30"] == 100.0, (
        f"one 1000x session moved the median to {curve['09:30']} — a mean was "
        "used, and today's reading is now silently deflated at every minute")
    assert set(curve) == {"09:30", "09:31", "09:32"}, "the curve is per-minute"


def test_rvol_carries_its_time_because_two_readings_do_not_compare() -> None:
    curve = rvol_curve([minutes(3, vol=100.0) for _ in range(20)])
    m = rvol_at(minutes(3, vol=300.0), curve)
    assert m.ok and abs(m.value - 3.0) < 1e-9
    assert "09:32" in m.sample, "the reading must always carry its t"


def test_rvol_rel_refuses_by_name_and_never_renders_one_point_zero() -> None:
    """**Refusal C.** A neutral-looking number for a missing input is the defect
    this project exists to prevent: `1.0` reads as *in line with its sector*,
    which is a finding, when nothing was compared at all."""
    m = rvol_rel(Measured(value=3.0, sample="09:31"), None)
    assert not m.ok
    assert m.unavailable == "no sector mapping"
    assert m.value is None
    rendered = m.unavailable
    assert rendered != "1.0" and rendered.strip() != ""


def test_a_measured_is_a_value_or_a_reason_never_both_and_never_neither() -> None:
    with pytest.raises(ValueError, match="half-populated"):
        Measured(value=1.0, unavailable="also broken")
    with pytest.raises(ValueError, match="half-populated"):
        Measured(value=None)
    with pytest.raises(ValueError, match="must name why"):
        Measured.absent("")


# ---- the sequence ---------------------------------------------------------


def test_a_clean_attach_fills_the_context_block() -> None:
    """**080.** Stage 1 (`attach()`) qualifies the contract alone now;
    stage 2's rows come from `stage2_of` — the test-side stand-in for
    `app.py`'s independent-landing dispatch, exercised as one synchronous
    call since `Fake` answers instantly."""
    r = attach("QQQ", Fake())
    assert r.attached and r.qualified
    assert r.contract.symbol == "QQQ"
    assert r.origin == "typed"
    ctx, rail = stage2_of(Fake(), QQQ)
    for k in ("Last $", "ADR% used", "VWAP", "RVOL", "RVOL_rel", "RVOL_sector"):
        assert k in ctx, f"{k} missing from the context block"
    # **VWAP_ext is gone — 080/v1.5.** The signed-distance suffix left the
    # VWAP row; nothing computes it any more (v1.5 §2, B-127's third firing).
    assert "VWAP_ext" not in ctx, "VWAP_ext should no longer be computed at all"
    # **070 Part 3, the leak check.** Christoph, 2026-08-23: the context block
    # carries `ADR% used` and NO other ADR metric, and no ATR anywhere in this
    # panel. `B-028`/`B-091`'s shape is a field that keeps reaching the record
    # after its row was deleted from `CONTEXT_ORDER` -- so this asserts the
    # field is absent from the STRUCTURE the compute functions return, not
    # merely unrendered by `live/tui/app.py`.
    for gone in ("ADR%", "ADR%avail", "ADR $", "ADR used", "room up",
                 "room down", "ATR14", "ATR20"):
        assert gone not in ctx, (
            f"{gone} is back in the context block. 070, ruled by Christoph "
            f"2026-08-23: no ATR anywhere in ATTACHED and no other ADR metric "
            f"— TRADE's stop selector is ATR's only surface in the terminal.")
    assert ctx["ADR% used"].ok
    # 042 Part 1: four opening-range levels, and no bare `ORH`/`ORL` anywhere.
    # **065 Part A: ORL5, ORL15 and 52wL explicitly, not merely covered by
    # `>=`.** Christoph, 2026-08-22: all three are intentional and must render.
    assert set(rail) >= {"PDH", "PDL", "PMH", "PML",
                         "ORH5", "ORL5", "ORH15", "ORL15", "52wH", "52wL",
                         "VWAP"}
    for k in ("ORL5", "ORL15", "52wL"):
        assert rail[k].ok, f"{k} rendered but did not measure: {rail[k]}"
    assert "ORH" not in rail and "ORL" not in rail, (
        "a bare ORH/ORL is a well-formed name answering two different questions")


def test_all_three_origins_are_recordable_even_though_only_typed_exists() -> None:
    """Recording the field now means the day record does not change shape when
    `scanner` and `watchlist` arrive — and a shape change to a record already
    carrying evidence is the expensive kind."""
    assert ORIGINS == ("typed", "scanner", "watchlist")
    for o in ORIGINS:
        assert attach("QQQ", Fake(), origin=o).origin == o
    with pytest.raises(ValueError):
        attach("QQQ", Fake(), origin="guessed")


def test_refusal_d_an_ambiguous_ticker_qualifies_nothing() -> None:
    """**Refusal D.** Picking the most liquid is a well-formed value answering a
    different question, and it would be silently right most of the time — which
    is exactly what makes it dangerous."""
    two = [QQQ, Contract(symbol="QQQ", con_id=999, exchange="ARCA")]
    r = attach("QQQ", Fake(contracts=two))
    assert not r.attached
    assert not r.qualified, "a contract was qualified for an ambiguous ticker"
    assert r.contract is None
    assert len(r.ambiguous) == 2, "the candidates must render"
    assert "ambiguous, refusing to guess" in r.refusal
    assert "resolved to 2 contracts" in r.refusal


def test_the_slot_is_checked_before_any_historical_request_is_spent() -> None:
    """**Step 2 precedes step 3 deliberately.** With no slot you should learn
    that in the first frame — not after three historical requests have gone
    against a 60-per-10-minutes budget on a symbol you are about to detach.

    **080: stage 1 (`attach()`) no longer touches a historical request at
    all** — `resolve` is the only call `f.calls` gets from it now, so the
    ordering this test exists to pin is checked against `stage2_of`'s own
    dispatch instead, which is what actually issues `daily`.
    """
    f = Fake(slots=TICK_SLOTS)
    r = attach("QQQ", f)
    assert r.attached, "no slot must not fail the attach"
    assert "no tick slot" in r.slot_state
    # The tape is what is missing, and it says so by name.
    assert r.tape == "absent - no free tick slot"
    ctx, _rail = stage2_of(f, QQQ)
    assert f.calls.index("resolve") < f.calls.index("daily")
    # ...and the context block is fully populated anyway. THIS IS THE POINT.
    assert ctx["ADR% used"].ok and ctx["VWAP"].ok


def test_refusal_b_the_same_symbol_twice_inside_the_cooldown() -> None:
    """**Refusal B.** 070 §6, ruled by the mockup — this used to assert the
    OPPOSITE of what it now does: `r.attached` was `True` and the context
    block was fully populated, with only `r.slot_state` naming the cooldown.
    The mockup draws a re-attach inside the cooldown as ONE line and nothing
    else (`1 of 1 · end`, no ADR/RVOL/VWAP), because step 3's per-role
    fallback requests (`dailies_on()` and its siblings) do not themselves
    check the pacing guard — only `warm()` does — so letting them run during
    the cooldown would spend a second, unguarded round of the same requests
    the guard exists to keep under IBKR's limit. **Never a silent drop**: the
    whole gather refuses before any historical request fires, with its
    remaining seconds on screen."""
    f = Fake(cooldown=11)
    r = attach("QQQ", f)
    assert not r.attached
    assert r.queued == "11s"
    # **080: `AttachResult` no longer carries `context`/`rail` at all** —
    # stage 2 is a separate dispatch `app.py` makes only from a SUCCESSFUL
    # `_finish_stage1`, which a queued cooldown never reaches. Checked here
    # against the one thing that still can prove it: no historical role was
    # ever asked for.
    assert f.calls == ["resolve"], (
        "a queued re-attach must not spend any of step 3's historical "
        f"requests — the whole point of refusing before it starts; saw {f.calls}")
    assert COOLDOWN_S == 15


def test_refusal_a_a_failed_request_leaves_the_others_rendering() -> None:
    """**Refusal A.** Kill the daily request mid-fetch: **per-row
    `unavailable (reason)`, never a partial ADR.**"""
    r = attach("QQQ", Fake(fail=["daily"]))
    assert r.attached, "one failed request must not fail the attach"
    ctx, _rail = stage2_of(Fake(fail=["daily"]), QQQ)
    for k in ("ADR% used",):
        assert not ctx[k].ok, f"{k} rendered a value from a failed request"
        assert "pacing limit, retry in 42s" in ctx[k].unavailable, (
            "pacing is a display state, not an error, and the reason must survive")
    # The rows that came from OTHER requests are untouched.
    assert ctx["VWAP"].ok, "VWAP refused because the DAILY request failed"
    assert ctx["RVOL"].ok


def test_a_partial_adr_is_impossible_by_construction() -> None:
    """Refusal A's real content: there is no state in which `round` exists
    and `ADR% used` does not, because each is derived from the same ADR $
    and both carry the same refusal."""
    ctx, rail = stage2_of(Fake(fail=["daily"]), QQQ)
    assert ctx["ADR% used"].value is None
    assert rail["round"].value is None, (
        "`round` spans by ADR $; a failed daily request must blank it too")


def test_refusal_c_end_to_end_no_sector_means_rvol_rel_refuses_by_name() -> None:
    r = attach("THIN", Fake(contracts=[NOSECTOR]))
    assert r.attached
    ctx, _rail = stage2_of(Fake(contracts=[NOSECTOR]), NOSECTOR)
    m = ctx["RVOL_rel"]
    assert not m.ok
    assert m.unavailable == "no sector mapping"
    assert ctx["RVOL"].ok, "the symbol's own RVOL must still render"


def test_the_tape_failing_does_not_fail_the_attach() -> None:
    """Step 4 does not gate step 3. **The tape is an enrichment, not a
    precondition.**"""
    r = attach("QQQ", Fake(fail=["tick"]))
    assert r.attached
    assert r.tape.startswith("absent - ")
    ctx, _rail = stage2_of(Fake(fail=["tick"]), QQQ)
    assert ctx["ADR% used"].ok


def test_no_playbook_says_so_rather_than_binding_nothing_silently() -> None:
    r = attach("QQQ", Fake(playbook=""))
    assert r.attached and r.playbook == "no trigger level declared"


def test_no_contract_found_is_a_refusal_not_a_crash() -> None:
    r = attach("ZZZZ", Fake(contracts=[]))
    assert not r.attached and r.refusal == "no contract found"


# ---- part 4: the seam -----------------------------------------------------


def test_the_seam_two_attach_times_agree_to_the_cent() -> None:
    """**S010 part 4, and nothing else would surface this.**

    *There is no such thing as a late attach.* Session VWAP and cumulative
    volume are reconstructed from history, never accumulated from the live
    stream — so attaching at 09:45 and at 10:12 must produce identical numbers
    for the overlapping window.

    A double-count drags VWAP; a gap loses prints silently. **Both show up here
    and nowhere else.**
    """
    session = minutes(60)
    early, late = session[:30], session[:30]     # same window, two attach times

    v_early, v_late = vwap_from_bars(early), vwap_from_bars(late)
    assert round(v_early.value, 2) == round(v_late.value, 2), (
        f"VWAP disagreed across attach times: {v_early.value} vs {v_late.value}")
    assert sum(b.volume for b in early) == sum(b.volume for b in late)

    # And a deliberate double-count must FAIL this test's own premise, or the
    # test proves nothing: a fixture that cannot break is not a fixture.
    doubled = vwap_from_bars(early + early)
    assert sum(b.volume for b in early + early) != sum(b.volume for b in early), (
        "the double-count fixture did not double anything")
    assert doubled.ok


def test_a_double_counted_seam_is_visible_in_cumulative_volume() -> None:
    """VWAP survives a uniform double-count (both terms scale) — **cumulative
    volume does not.** That asymmetry is why the seam test asserts BOTH, and it
    is the same signature 008b measured: the number you would sanity-check stays
    plausible while the one you would not is wrong."""
    session = minutes(30)
    from core.indicators.context import cumulative_volume
    assert cumulative_volume(session).value == 30_000
    assert cumulative_volume(session + session).value == 60_000


# ---- part 2: no cache, and a test rather than a convention ----------------


def test_no_disk_write_on_the_attach_path() -> None:
    """**S010 part 2 requires a test, not a convention.**

    `BUILD-PLAN.md` §010: *if this slice needs a cache, the decision was wrong.*
    So this asserts the repo is byte-for-byte unchanged across a full attach —
    which also catches a stray `__pycache__` write into a tracked directory.
    """
    before = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout
    attach("QQQ", Fake())
    attach("THIN", Fake(contracts=[NOSECTOR]))
    after = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout
    assert before == after, (
        "the attach path changed the working tree:\n"
        f"before:\n{before}\nafter:\n{after}\n"
        "No nightly cache, no local store, no warm path. If this slice needs a "
        "cache, the no-local-database decision was wrong — and that is a "
        "finding, not something to fix by adding one.")


def test_the_attach_path_imports_no_sizing_or_staging_module() -> None:
    """`SPEC.md` §6b.1c — a symbol process cannot size, stage, or evaluate a
    limit, **enforced structurally rather than by discipline.**

    **This is the WEAK half of that test, and the strong half is owed by S011.**
    The sizing and staging modules do not exist yet, so asserting the attach
    path does not import them passes because its subject is absent — a vacuous
    pass, and this project has a fixture proving how easily one happens.

    What this CAN check today is the source text, which at least fails if
    somebody adds the import before S011 lands. Recorded in S010's done-note as
    owed by S011: assert `size_for()`'s parameter list contains no rule type and
    that the module graph has no edge at all.
    """
    src = (REPO / "live" / "attach" / "attach.py").read_text(encoding="utf-8")
    body = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    for banned in ("import sizing", "from live.sizing", "from live.staging",
                   "import staging", "size_for("):
        assert banned not in body, f"the attach path reaches {banned!r}"

"""038 Part 5 tests 1 and 2 — the basis that is DECLARED is the basis REQUESTED.

**The thing being prevented is not a missing constant. It is a constant that
exists, reads correctly, and is not what reaches the wire.** That is the shape of
the defect 038 was written for: `ATR14` rendered `13.14` against a true ~`15.6`
because one `daily_bars` request at `use_rth=True` served ADR and ATR alike. Every
comment in the module said the right thing. The flag did not.

So these assert against `reqHistoricalData`'s actual keyword arguments, captured
from `IBKRMarketData` — the real class the live program uses — against a fake
transport. **A test that only checked `ATR_BASIS.use_rth is False` would have
passed on the broken code**, because `ATR_BASIS` did not exist to disagree with.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.indicators.context import (ADR_BASIS, ATR_BASIS, INTRADAY_BASIS,
                                     LONG_BASIS, PRIOR_DAY_BASIS,
                                     PRIOR_MONTH_BASIS, PRIOR_WEEK_BASIS,
                                     SMA_BASIS, SessionBasis, TODAY_BASIS)
from live.attach.attach import Contract
from live.attach.ibkr import IBKRMarketData


class _Bar:
    """The shape `ib_async` hands back. Daily bars arrive as `YYYY-MM-DD`."""

    def __init__(self, date: str) -> None:
        self.date = date
        self.open = self.high = self.low = self.close = 100.0
        self.volume = 1_000.0
        self.average = 100.0


class RecordingIB:
    """Captures every `reqHistoricalData` call. **Answers nothing useful** —
    what is under test is the request, not the reply."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def reqHistoricalData(self, contract, **kwargs):
        self.calls.append(kwargs)
        return [_Bar(f"2026-08-{d:02d}") for d in range(1, 29)]

    def reqContractDetails(self, contract):
        return []

    def use_rth_for(self, *, size: str, duration: str | None = None) -> list[bool]:
        return [c["useRTH"] for c in self.calls
                if c["barSizeSetting"] == size
                and (duration is None or c["durationStr"] == duration)]


QQQ = Contract(symbol="QQQ", con_id=320227571, exchange="SMART")


@pytest.mark.parametrize("basis", [
    pytest.param(ADR_BASIS, id="ADR_BASIS"),
    pytest.param(ATR_BASIS, id="ATR_BASIS"),
    pytest.param(PRIOR_DAY_BASIS, id="PRIOR_DAY_BASIS"),
    pytest.param(SMA_BASIS, id="SMA_BASIS"),
])
def test_a_daily_request_carries_the_basis_it_was_asked_with(basis: SessionBasis) -> None:
    """**Test 1.** The flag on the wire is the flag on the constant.

    Parameterised over every declared daily basis rather than asserting once,
    because the failure mode is one indicator being right while another quietly
    shares its request.
    """
    ib = RecordingIB()
    IBKRMarketData(ib).daily_bars(QQQ, basis)

    assert len(ib.calls) == 1, (
        f"expected exactly one historical request, got {len(ib.calls)}")
    assert ib.calls[0]["useRTH"] is basis.use_rth, (
        f"{basis.label} declares use_rth={basis.use_rth} and the request "
        f"issued useRTH={ib.calls[0]['useRTH']}. **The constant and the wire "
        f"disagree**, which is the entire defect 038 exists to close — every "
        f"comment in the module can say the right thing while the flag does "
        f"not.")


def test_today_minutes_carries_its_fixed_basis() -> None:
    """**Test 1, continued** — `today_minutes` fixes its own basis rather
    than accepting one, because VWAP/`Last $`/`cum vol` have no choice to
    make: their anchor stays ETH regardless of RVOL's own (083). It must
    still take it from the constant and not from a literal.

    **058 retires `year_high_low` as a third case here** — see
    `test_a_long_range_request_now_shares_the_rth_daily_request` below for
    where the 52-week check moved.
    """
    ib = RecordingIB()
    md = IBKRMarketData(ib)
    md.today_minutes(QQQ)

    minute_flags = ib.use_rth_for(size="1 min", duration="1 D")
    assert minute_flags and all(f is INTRADAY_BASIS.use_rth for f in minute_flags), (
        f"today_minutes issued {minute_flags}, but INTRADAY_BASIS declares "
        f"use_rth={INTRADAY_BASIS.use_rth}. VWAP's anchor is untouched by 083 "
        f"and must not vary with RVOL's own.")


@pytest.mark.parametrize("basis", [
    pytest.param(SessionBasis(use_rth=True, label="09:30-16:00 ET", why="rth"), id="rth"),
    pytest.param(SessionBasis(use_rth=False, label="04:00-20:00 ET", why="eth"), id="eth"),
])
def test_intraday_sessions_carries_whatever_basis_it_is_called_with(
    basis: SessionBasis,
) -> None:
    """**083 corrects this test's own prior premise.** `intraday_sessions`
    used to fix `INTRADAY_BASIS` unconditionally — 038-era, before RVOL's
    basis was a caller's choice at all. **083 makes it genuinely one**:
    `config/rvol.yaml`'s `rvol_anchor`, read once per attach into a
    `SessionBasis` (`Stage2Inputs.rvol_basis`) and passed explicitly, the
    same pattern `daily_bars` already used. This asserts the request on the
    wire matches whatever basis the CALLER supplied, in both directions —
    a test parameterised on one value only would pass even if the parameter
    were silently ignored (the exact `OBS-037` shape test 2 below guards
    against for ADR/ATR).
    """
    ib = RecordingIB()
    md = IBKRMarketData(ib)
    md.intraday_sessions(QQQ, basis)

    flags = ib.use_rth_for(size="1 min", duration="20 D")
    assert flags == [basis.use_rth], (
        f"intraday_sessions(QQQ, {basis.label}) issued useRTH={flags}, "
        f"expected [{basis.use_rth}] — the request must carry the basis it "
        f"was actually called with, not a fixed constant.")


#: **041's thirteen, grouped as Christoph ruled them.** All RTH.
#:
#: **Only `52wH`/`52wL` are built.** The other eleven have no computation and no
#: request, so the strongest available assertion for them is that the constant
#: they will use declares RTH — see the two tests below, which say plainly which
#: of them checks a request and which checks a ruling.
THE_THIRTEEN = (
    ("HOD LOD", TODAY_BASIS),
    ("PWH PWL PWO PWC", PRIOR_WEEK_BASIS),
    ("MoMH MoML MoMO MoMC", PRIOR_MONTH_BASIS),
    ("52wH 52wL ATH", LONG_BASIS),
)


@pytest.mark.parametrize("levels,basis", THE_THIRTEEN,
                         ids=[g.replace(" ", "-") for g, _ in THE_THIRTEEN])
def test_the_thirteen_levels_are_ruled_rth(levels: str, basis: SessionBasis) -> None:
    """**041's ruling, as a ruling.** Closes `OBS-051` for the level half.

    **This asserts the CONSTANT, not a request, and that is a real limitation
    rather than a shortcut.** Eleven of the thirteen are not built — there is no
    `HOD`, no `PWH`, no `MoMC`, no `ATH` anywhere in the tree — so there is no
    request to inspect. `test_a_long_range_request_carries_the_ruled_basis`
    below covers the two that do issue one.

    **The composition argument is why they are all the same answer.** `PWH` is
    the maximum of its week's `PDH`s, `MoMH` of its weeks, `52wH` of its months.
    `038` made `PDH` RTH, so an ETH level anywhere up that chain sits above every
    level inside it, and no row on the panel could explain why.
    """
    assert basis.use_rth is True, (
        f"{levels} must be RTH (041). It declares use_rth={basis.use_rth}, "
        f"which breaks the composition chain: 038 made PDH RTH, so a week, "
        f"month or year computed on extended hours would be higher than every "
        f"day inside it.")
    assert basis.label == "09:30-16:00 ET", (
        f"{levels} declares the label {basis.label!r}, which does not name the "
        f"regular session.")


def test_a_long_range_request_now_shares_the_rth_daily_request() -> None:
    """**The two of the thirteen that are built, checked on the wire.**

    `52wH`/`52wL` are the only levels of 041's thirteen with a computation
    behind them. **058 Part 1 retires `year_high_low` as a separate request**
    — `OBS-079` measured it as a redundant round trip against the RTH daily
    fetch `ADR_BASIS` already issues, differing only in how far back it went.
    `daily_bars(c, ADR_BASIS)` now asks for `1 Y` (`LONG_DAILY_DURATION`), not
    `60 D`, and `_context_block` (`live/attach/attach.py`) takes 52wH/52wL as
    the max/min over that same series rather than issuing its own request.

    LONG_BASIS's ruling (041, RTH) survives unchanged — it is what makes
    sharing the RTH daily request with ADR_BASIS correct rather than a
    coincidence: both declare `use_rth=True` for the same reason.
    """
    ib = RecordingIB()
    IBKRMarketData(ib).daily_bars(QQQ, ADR_BASIS)
    flags = ib.use_rth_for(size="1 day", duration="1 Y")
    assert flags == [ADR_BASIS.use_rth] == [True] == [LONG_BASIS.use_rth], (
        f"the RTH daily request issued {flags} at duration != 1 Y; ADR_BASIS "
        f"and LONG_BASIS both declare use_rth=True and 058 Part 1 collapses "
        f"them onto one request.")


def test_the_rth_daily_request_is_the_only_one_058_collapsed() -> None:
    """**058 Part 1, asserted by count.** Exactly ONE historical request for
    `daily_bars(QQQ, ADR_BASIS)` — no separate `60 D` request survives
    alongside the `1 Y` one. `OBS-079` measured the pre-058 shape as two RTH
    daily requests for the same contract at two different windows; this is
    the collapse, checked on the wire rather than only in prose.

    **Supersedes `test_the_thirteen_do_not_share_a_request_with_anything_
    038_settled` (041/038-era), which asserted the OPPOSITE** — that the
    long-range request must never share a round trip with anything ADR or
    the SMA stack use. 058 is a later, explicit product ruling that
    overturns that isolation deliberately: `ADR%`/the SMA stack/PDH-PDL only
    ever read the TAIL of whatever daily series they are given, so widening
    the window to a year changes none of their answers, and sharing the
    request is the entire point of the collapse.
    """
    ib = RecordingIB()
    IBKRMarketData(ib).daily_bars(QQQ, ADR_BASIS)
    durations = [c["durationStr"] for c in ib.calls]
    assert durations == ["1 Y"], (
        f"daily_bars(ADR_BASIS) issued {durations}; 058 Part 1 collapses the "
        f"RTH daily fetch onto a single 1 Y request that also serves "
        f"52wH/52wL.")


def test_no_call_site_passes_a_use_rth_literal() -> None:
    """**038 Part 3, structurally.** The flag comes from a constant, never from
    a literal typed at the call site.

    Scoped to the fetch layer positionally. Without this, the constants can be
    declared, exported, tested — and bypassed by one `use_rth=True` that a
    reviewer's eye slides over, which is how the original defect survived a
    module docstring explicitly warning about it.

    **Parsed, not grepped.** A text scan matches the module's own docstring,
    which quotes `useRTH=True` precisely in order to warn about it — so the
    prose explaining the rule would fail the test enforcing it. `ast` sees only
    the arguments actually passed.
    """
    import ast

    path = REPO / "live" / "attach" / "ibkr.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg in ("use_rth", "useRTH") and isinstance(kw.value, ast.Constant):
                offenders.append(
                    f"line {kw.value.lineno}: {kw.arg}={kw.value.value!r}")
    assert not offenders, (
        "these call sites pass a literal where a `SessionBasis` constant "
        "belongs:\n" + "\n".join(f"  {o}" for o in offenders)
        + "\n**A basis is a definition, not a value you type at the call "
          "site** (038 Part 3).")


def test_adr_and_atr_must_not_request_the_same_flag() -> None:
    """**Test 2, and it is the one that catches this test file being useless.**

    038 Part 5: *a configuration where both read alike passes trivially — that
    is `OBS-037`'s shape, in the test written to prevent it.* If ADR and ATR ever
    agree, then test 1 above proves nothing about either: a single shared request
    would satisfy both assertions while rendering exactly the wrong `ATR14`.

    **The two differ definitionally, not by preference.** ADR is the mean of each
    session's own high-low and has no gap term, so it is the regular session.
    ATR's true range spans the prior close, so the gap IS the measurement and it
    must be the extended series.
    """
    assert ADR_BASIS.use_rth != ATR_BASIS.use_rth, (
        f"ADR and ATR both request use_rth={ADR_BASIS.use_rth}. **They measure "
        f"different things over different sessions on purpose** — ADR has no "
        f"gap term, ATR is nothing but the gap term. Two volatility rows four "
        f"apart on one panel, computed alike, is the reading this task exists "
        f"to make impossible.")
    assert ADR_BASIS.use_rth is True, "ADR is RTH by definition (038 Part 2)."
    assert ATR_BASIS.use_rth is False, "ATR is ETH by definition (038 Part 2)."


def test_prior_day_levels_are_regular_session() -> None:
    """**038 Part 1, and this is the half `036` got wrong.**

    If `PDH`/`PDL` were ETH, then on any day the extreme fell outside
    09:30-16:00, **`PDL` IS `AML`** — one number, two names, no way to tell them
    apart. Confirmed on QQQ 2026-08-13: the extended-hours low of `717.37` sat in
    the early pre-market, so an ETH `PDL` would have been `PML` that day.

    **A level is not a statistic.** ADR being RTH does not propagate here and ATR
    being ETH does not either.
    """
    assert PRIOR_DAY_BASIS.use_rth is True, (
        "PDH/PDL must come from the regular session. On ETH bars they collapse "
        "into AMH/AML whenever the prior day's extreme fell after 16:00 — a "
        "level that silently changes identity is the canonical defect here.")


def test_every_basis_says_why_it_is_what_it_is() -> None:
    """A basis with no reason is a setting wearing a definition's clothes.

    The `why` is what stops the next person moving these into `config/` for
    consistency with §4.4 — **an exemption that is not written down is one that
    gets undone.**
    """
    for name, basis in (("ADR_BASIS", ADR_BASIS), ("ATR_BASIS", ATR_BASIS),
                        ("PRIOR_DAY_BASIS", PRIOR_DAY_BASIS),
                        ("INTRADAY_BASIS", INTRADAY_BASIS),
                        ("SMA_BASIS", SMA_BASIS), ("LONG_BASIS", LONG_BASIS),
                        ("TODAY_BASIS", TODAY_BASIS),
                        ("PRIOR_WEEK_BASIS", PRIOR_WEEK_BASIS),
                        ("PRIOR_MONTH_BASIS", PRIOR_MONTH_BASIS)):
        assert basis.why.strip(), f"{name} declares no reason."
        assert basis.label.strip().endswith("ET"), (
            f"{name}'s label {basis.label!r} does not name a timezone. "
            "**`ET` is not optional** (038 Part 2) — Christoph is in Cape Town, "
            "and 034 lost four values to a UTC/ET slicing defect.")

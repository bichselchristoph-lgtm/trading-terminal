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
                                     PRIOR_DAY_BASIS, SMA_BASIS, SessionBasis,
                                     YEAR_BASIS)
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


def test_the_intraday_and_year_requests_carry_their_declared_bases() -> None:
    """**Test 1, continued** — the three calls that do not take a basis argument.

    `today_minutes`, `intraday_sessions` and `year_high_low` fix their own basis
    rather than accepting one, because no caller has a choice to make. They must
    still take it from the constant and not from a literal.
    """
    ib = RecordingIB()
    md = IBKRMarketData(ib)
    md.today_minutes(QQQ)
    md.intraday_sessions(QQQ)
    md.year_high_low(QQQ)

    minute_flags = ib.use_rth_for(size="1 min")
    assert minute_flags and all(f is INTRADAY_BASIS.use_rth for f in minute_flags), (
        f"a 1-minute request issued {minute_flags}, but INTRADAY_BASIS declares "
        f"use_rth={INTRADAY_BASIS.use_rth}. **Both sides of RVOL must share a "
        f"basis** — an RTH curve under an ETH numerator has no key past the "
        f"close.")

    year_flags = ib.use_rth_for(size="1 day", duration="1 Y")
    assert year_flags == [YEAR_BASIS.use_rth], (
        f"the 52-week request issued {year_flags}, YEAR_BASIS declares "
        f"use_rth={YEAR_BASIS.use_rth}.")


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
                        ("SMA_BASIS", SMA_BASIS), ("YEAR_BASIS", YEAR_BASIS)):
        assert basis.why.strip(), f"{name} declares no reason."
        assert basis.label.strip().endswith("ET"), (
            f"{name}'s label {basis.label!r} does not name a timezone. "
            "**`ET` is not optional** (038 Part 2) — Christoph is in Cape Town, "
            "and 034 lost four values to a UTC/ET slicing defect.")

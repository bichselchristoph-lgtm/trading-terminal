"""088 — ADR% used reads 106.8% at an 04:00 attach. Part 0's three reads,
each confirmed by reading the wire path rather than by running the terminal:

1. **Which request supplies the numerator/denominator terms, and what window
   does it actually return at an 04:00 attach?** `ibkr.py`'s `daily_bars`
   for `ADR_BASIS` issues `useRTH=True`, `durationStr=LONG_DAILY_DURATION`
   (1 Y), `barSizeSetting="1 day"`, `endDateTime=""` — IBKR's own "now".
   Before today's RTH session has printed a trade, that request has nothing
   for today at all, so the LAST bar it returns is the last COMPLETED
   session. `attach.py`'s `_adr_terms`/`compute_context_and_rail` read
   `rth_dailies[-1]` unconditionally as "today" — `todays_open =
   rth_dailies[-1].open`, `current = rth_dailies[-1].close` — with nothing
   checking whether that bar's date IS today's.

2. **Is that window today's session in progress, or the last completed
   one?** At a pre-open attach: the last completed one. There is no
   partial-today reading in the pre-open request at all — `rth_dailies[-1]`
   is a whole, closed session, wearing "today" as an assumption rather than
   a checked fact.

3. **Which basis does the numerator use, against a denominator labelled
   `ADR20 RTH`?** The SAME one. `adr_used(inp.rth_dailies[-1].close,
   todays_open, dol)` — `current`, `todays_open` and `dol` (via `_adr_terms`
   -> `adr_pct`/`adr_dollar`, both `ADR_BASIS`) are all built from the
   identical `rth_dailies` list, `ADR_BASIS` (`useRTH=True`) throughout.
   **No second object, no second flag — Candidate B does not hold.** There
   is nothing here for a Divergence (object-identity) test to guard, because
   there was never a second basis to diverge from the first; that is why
   this file has no Divergence test where 083's did.

**Candidate A is what produced 106.8%.** A whole completed session's own
`high - low` — sorry, `close - open` here, since `adr_used` measures
distance travelled, not range — divided by a 20-session ADR$ average lands
near 100% by construction (a session's own move is ordinarily close to its
own trailing average), and 106.8% is one ordinary day above that average,
not a multi-day accumulation. **ADR%'s basis is fixed by arithmetic, exactly
as 083 assumed when it excluded ADR% from its own scope** — this is not a
second instance of B-049's shape (that was two independently-read flags that
happened to agree; this is one flag, one object, read once, just read at the
wrong INSTANT).
"""
from __future__ import annotations

from core.indicators.context import ADR_BASIS, Bar, Measured

from live.attach.attach import Stage2Inputs, compute_context_and_rail
from live.tui.app import context_rows
from live.tui.day_record import Attached

#: The last COMPLETED RTH session, as `rth_dailies[-1]` reads at a pre-open
#: attach on `TODAY_ET` — three calendar days back is arbitrary; only "not
#: `TODAY_ET`" matters.
LAST_COMPLETE_SESSION = "2026-08-21"
#: Today's ET calendar date — what `app.py`'s `_begin_attach` would have
#: captured, per 088's own fix.
TODAY_ET = "2026-08-24"


def _dailies(n: int = 25, *, last_date: str = TODAY_ET) -> list[Bar]:
    """`n` daily bars, oldest-first, ending on `last_date` — enough for
    `adr_pct`'s default `n=20` (needs 21) with headroom. Every session
    carries a distinct, ordinary `high/low` so `adr_pct`'s mean is a real
    number, not a degenerate one."""
    from datetime import date, timedelta
    end = date.fromisoformat(last_date)
    out = []
    for i in range(n):
        d = end - timedelta(days=(n - 1 - i))
        wobble = 0.5 + (i % 3) * 0.25       # a little session-to-session spread
        out.append(Bar(ts=d.isoformat(), open=100.0, high=100.0 + wobble,
                       low=100.0 - wobble, close=100.0 + (wobble / 2),
                       volume=1_000_000))
    return out


# ---- Green — a mid-session attach computes, on the same object throughout -


def test_green_last_bar_dated_today_computes_the_row() -> None:
    """`rth_dailies[-1]`'s date matches `today_et` — the mid-session shape
    (or a post-close attach the same calendar day): the row computes, and
    Part 0 item 3's read is asserted directly — numerator and denominator
    both trace to `ADR_BASIS`, the one object, not two that agree."""
    inp = Stage2Inputs(today_et=TODAY_ET)
    inp.rth_dailies = _dailies(last_date=TODAY_ET)
    ctx, _rail = compute_context_and_rail(inp)
    assert ctx["ADR% used"].ok, ctx["ADR% used"].unavailable
    assert ctx["ADR% used"].basis is ADR_BASIS, (
        "the numerator's basis must be the SAME object as ADR's own "
        "denominator basis — Part 0 item 3")


def test_green_no_today_et_preserves_the_pre_088_behaviour() -> None:
    """`today_et == ""` (every `Stage2Inputs()` built before this task, and
    every existing test that never learned about it) skips the day-boundary
    check entirely — the deliberate escape hatch that lets 088 land without
    retrofitting a wall-clock date onto tests that were never about one."""
    inp = Stage2Inputs()                    # today_et defaults to ""
    inp.rth_dailies = _dailies(last_date=LAST_COMPLETE_SESSION)
    ctx, _rail = compute_context_and_rail(inp)
    assert ctx["ADR% used"].ok, (
        "with no today_et supplied, the row must compute exactly as it did "
        "before 088 — the escape hatch this task deliberately leaves open")


# ---- Refusal — the row that would have shown 106.8% now refuses -----------


def test_refusal_pre_open_attach_refuses_rather_than_reading_a_closed_session() -> None:
    """The exact reproduction: `rth_dailies[-1]` is `LAST_COMPLETE_SESSION`,
    `today_et` is `TODAY_ET` — the 04:00 attach shape. The row must refuse,
    not compute a plausible-looking percentage over a session that already
    closed."""
    inp = Stage2Inputs(today_et=TODAY_ET)
    inp.rth_dailies = _dailies(last_date=LAST_COMPLETE_SESSION)
    ctx, _rail = compute_context_and_rail(inp)
    m = ctx["ADR% used"]
    assert not m.ok
    assert m.unavailable == "session not started", (
        f"expected the RVOL-precedent refusal wording, got {m.unavailable!r}")


def test_refusal_rendered_text_is_exact_not_a_substring() -> None:
    """**B-126.** The specific rendered row, not a substring check."""
    a = Attached(symbol="QQQ", since="04:00:50", context={
        "ADR% used": Measured.absent("session not started")})
    row = next(r for r in context_rows(a) if "ADR% used" in r)
    assert row.strip() == "ADR% used    — (session not started)", (
        f"exact wording mismatch:\n{row!r}")


def test_refusal_three_states_are_distinguishable() -> None:
    """**Not two states, three.** A computed value, a fetch failure
    (`rth_dailies_failed`), and the new day-boundary refusal must each
    render differently — a reader (or a test) cannot mistake one for
    another."""
    computed = Stage2Inputs(today_et=TODAY_ET)
    computed.rth_dailies = _dailies(last_date=TODAY_ET)
    computed_ctx, _ = compute_context_and_rail(computed)
    computed_row = next(r for r in context_rows(
        Attached(symbol="QQQ", since="09:31:00",
                context={"ADR% used": computed_ctx["ADR% used"]}))
        if "ADR% used" in r)

    not_started = Stage2Inputs(today_et=TODAY_ET)
    not_started.rth_dailies = _dailies(last_date=LAST_COMPLETE_SESSION)
    not_started_ctx, _ = compute_context_and_rail(not_started)
    not_started_row = next(r for r in context_rows(
        Attached(symbol="QQQ", since="04:00:50",
                context={"ADR% used": not_started_ctx["ADR% used"]}))
        if "ADR% used" in r)

    failed = Stage2Inputs(today_et=TODAY_ET)
    failed.rth_dailies_failed = "pacing limit, retry in 42s"
    failed_ctx, _ = compute_context_and_rail(failed)
    failed_row = next(r for r in context_rows(
        Attached(symbol="QQQ", since="09:31:00",
                context={"ADR% used": failed_ctx["ADR% used"]}))
        if "ADR% used" in r)

    rows = {computed_row, not_started_row, failed_row}
    assert len(rows) == 3, f"two states rendered alike:\n{rows}"
    assert "session not started" in not_started_row
    assert "session not started" not in failed_row
    assert "pacing limit" in failed_row


# ---- Boundary — the rollover itself, not an assumption about it -----------


def test_boundary_the_last_minute_before_and_the_first_minute_after() -> None:
    """**The case that produced the defect, tested directly rather than
    assumed.** One `Stage2Inputs`, `today_et` fixed at `TODAY_ET`; only
    `rth_dailies[-1]`'s own date moves across the boundary — refuses right
    up to the instant IBKR's daily bar is dated today, computes from the
    instant it is."""
    inp = Stage2Inputs(today_et=TODAY_ET)

    inp.rth_dailies = _dailies(last_date=LAST_COMPLETE_SESSION)   # before
    before_ctx, _ = compute_context_and_rail(inp)
    assert not before_ctx["ADR% used"].ok, (
        "one bar short of today's date must still refuse")

    inp.rth_dailies = _dailies(last_date=TODAY_ET)                # after
    after_ctx, _ = compute_context_and_rail(inp)
    assert after_ctx["ADR% used"].ok, (
        "the instant the daily bar is dated today, the row must compute")


# ---- Fixture — every state above is self-constructed ----------------------


def test_fixture_this_file_builds_every_state_itself() -> None:
    """**B-136, checked as code, not trusted by review.** No import from
    `test_attach.py` or `test_080_two_stage_attach.py` — every
    `Stage2Inputs`/`Attached`/`Bar` above is hand-built here."""
    import ast
    from pathlib import Path
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (
            "test_attach" in node.module or "test_080" in node.module
        ):
            names.update(a.name for a in node.names)
    assert not names, f"this file imports fixtures from another test file ({names})"

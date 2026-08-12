"""The observations ledger has a trigger, or it is a folder nobody opens.

**016 part 5c.** `docs/observations/` existed as a folder and nothing said how
anything left it. Findings were captured in done-notes and never acted on
because **there was no mechanism** — which is the project's most-named failure
applied to the machinery for handling the project's failures.

Built on the shape of `test_open_questions.py`, with its one hard-won lesson
carried across:

**DELETING A ROW MUST NOT CLEAR IT.** An earlier version of that test keyed on a
folder being non-empty, which made deletion the cheapest route to green on a
mechanism whose entire purpose was holding things open. Here the row count is
pinned against a floor recorded in this file, so removing a row fails rather
than passes. **`PROMOTED` or `DROPPED` with a `resolution:` is the only exit.**

**Red for being IGNORED, not for being open.** A test that goes red the moment a
finding is recorded teaches people not to record findings. This one goes red
when an `OPEN` row passes its `review-by` date — the date is the promise, and
the test enforces the promise rather than the state.

**Missing or malformed `review-by` is red. Unknown is never read as answered** —
the same rule, and for the same reason, as the handoff-state header test.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "docs" / "observations" / "OBSERVATIONS.md"

STATUSES = ("OPEN", "PROMOTED", "DROPPED")
RESOLVED = ("PROMOTED", "DROPPED")

#: US/Eastern, like every other date decision in this project. A ledger that
#: turned red at a different instant depending on the machine's locale would be
#: a worse instrument than no ledger.
EASTERN = ZoneInfo("America/New_York")

#: **The floor, not the count.** The ledger was seeded with 13 rows under 016.
#: Rows may be ADDED freely; the number may never go down, because a row is
#: resolved by changing its status, never by removal. **If this number is ever
#: lowered to make the suite green, that is the failure this test exists to
#: prevent, performed deliberately.**
SEEDED_ROWS = 13

#: A data row: `| **OBS-001** | 2026-08-11 | KIND | ... |`. Positional — the id
#: must be in the FIRST cell, so a row discussed in prose is not a row.
ROW = re.compile(
    r"^\|\s*\*{0,2}(?P<id>OBS-\d{3})\*{0,2}\s*\|(?P<rest>.+)\|\s*$", re.M)


def cells(rest: str) -> list[str]:
    return [c.strip() for c in rest.split("|")]


def rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for m in ROW.finditer(LEDGER.read_text(encoding="utf-8")):
        c = cells(m.group("rest"))
        out.append({"id": m.group("id"), "cells": c,
                    "status": c[-2].strip("* ").upper() if len(c) >= 2 else "",
                    "review_by": c[-1].strip("* ") if c else ""})
    return out


def today() -> dt.date:
    return dt.datetime.now(EASTERN).date()


def parse_review_by(raw: str) -> dt.date | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw or ""):
        return None
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        return None


# ---- the ledger exists and is well formed ---------------------------------


def test_the_ledger_exists() -> None:
    assert LEDGER.exists(), (
        f"{LEDGER.relative_to(REPO)} is missing. The ledger IS the mechanism — "
        "without it, findings live in done-notes nobody reopens.")


def test_deleting_a_row_does_not_clear_it() -> None:
    """**The lesson from `test_open_questions.py`, carried across.**

    That gate once keyed on a folder being non-empty, which made deleting the
    file the cheapest route to green on a mechanism whose purpose was holding
    things open. Pinning a floor means removal fails instead.
    """
    n = len(rows())
    assert n >= SEEDED_ROWS, (
        f"the ledger has {n} rows; it was seeded with {SEEDED_ROWS} and the count "
        "may never go down.\n\n"
        "A ROW IS RESOLVED BY CHANGING ITS STATUS TO PROMOTED OR DROPPED WITH A "
        "`resolution:`, NEVER BY DELETING IT. Deleting one silently loses the "
        "fact that somebody once thought it mattered — which is the whole thing "
        "this ledger exists to stop.")


@pytest.mark.parametrize("field", ["status", "review_by"])
def test_every_row_declares_the_field(field: str) -> None:
    missing = [r["id"] for r in rows() if not r[field]]
    assert not missing, f"rows with no {field}: {missing}"


def test_every_status_is_one_of_the_three() -> None:
    wrong = [(r["id"], r["status"]) for r in rows() if r["status"] not in STATUSES]
    assert not wrong, (
        f"rows with a status outside {STATUSES}: {wrong}. The vocabulary is closed — "
        "a fourth value is a way of being neither open nor resolved.")


def test_every_review_by_is_a_real_date() -> None:
    """**Unknown is never read as answered.** A malformed date cannot be compared,
    and a comparison that silently passes is worse than no comparison."""
    bad = [(r["id"], r["review_by"]) for r in rows() if parse_review_by(r["review_by"]) is None]
    assert not bad, (
        f"rows with a missing or malformed review-by (want YYYY-MM-DD): {bad}\n"
        "An unparseable date is RED, deliberately. It cannot be compared, so "
        "treating it as satisfied would make the trigger silently inert.")


# ---- the trigger ----------------------------------------------------------


def test_no_open_row_is_past_its_review_date() -> None:
    """**THE TRIGGER. Red for being ignored, not for being open.**

    Clear it by *deciding*: set `PROMOTED` or `DROPPED` and write a
    `resolution:` naming where it went or why it did not. Moving the date is
    also legitimate — but it is a decision someone makes and can be seen making
    in `git log`, which is the point.
    """
    now = today()
    overdue = []
    for r in rows():
        if r["status"] != "OPEN":
            continue
        d = parse_review_by(r["review_by"])
        if d is not None and d < now:
            overdue.append(f"{r['id']}  review-by {r['review_by']}  ({(now - d).days} days ago)")
    assert not overdue, (
        "these observations are OPEN past their review-by date:\n  "
        + "\n  ".join(overdue)
        + "\n\nThis is NOT red for being open. It is red for being IGNORED.\n"
          "Clear it by deciding: PROMOTED or DROPPED with a `resolution:` line, or "
          "move the\ndate deliberately. DELETING THE ROW DOES NOT CLEAR IT and must "
          "not be made to.")


def test_every_resolved_row_has_a_resolution() -> None:
    """`PROMOTED` and `DROPPED` are claims that something happened. A claim with
    no statement of what happened is a status field being used as an off switch."""
    text = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""
    missing = []
    for r in rows():
        if r["status"] not in RESOLVED:
            continue
        block = re.search(rf"\*\*{r['id']}\b[^\n]*\*\*\s*\n\s*`resolution:`", text)
        if not block:
            missing.append(r["id"])
    assert not missing, (
        f"rows marked PROMOTED or DROPPED with no `resolution:` under a "
        f"**{'{id}'}** heading in the Resolutions section: {missing}\n"
        "Name where it went, or why it did not. Otherwise the status is an off "
        "switch with no record behind it.")


# ---- the trigger actually triggers ----------------------------------------


def test_the_trigger_fires_on_a_past_date() -> None:
    """A trigger nobody has seen fire is a trigger nobody should trust.

    Exercised against the parsing helpers rather than by writing to the real
    ledger — a test that mutates the artifact it guards can leave the tree dirty
    when it fails, which is how a guard becomes the thing that needs guarding.
    """
    past = today() - dt.timedelta(days=1)
    assert parse_review_by(past.isoformat()) == past
    assert parse_review_by(past.isoformat()) < today(), "a past date must compare as overdue"
    for malformed in ("", "soon", "2026-13-01", "12/11/2026", "2026-11"):
        assert parse_review_by(malformed) is None, (
            f"{malformed!r} parsed as a date; malformed must be RED, not tolerated")


def test_a_reading_is_distinguishable_from_an_observation() -> None:
    """016 §5b: *"mark clearly which are observations and which are readings."*

    `012` came within one sentence of recording Cboe One odd-lot filtering as
    the established cause of a 5.32x discrepancy. It is not established, and a
    ledger that cannot hold that distinction would launder it into one.
    """
    kinds = {r["cells"][1].upper() for r in rows() if len(r["cells"]) > 1}
    assert any("READING" in k for k in kinds), (
        "no row is marked READING. The distinction between what was measured and "
        "what was inferred is not decoration — it is what stops a plausible "
        "explanation being read later as a finding.")
    assert any("OBSERVATION" in k for k in kinds)


def test_every_row_cites_a_source() -> None:
    """*"A finding with no source does not go in."* The `what produced it` column
    is index 3 and must name a file or a session."""
    thin = [r["id"] for r in rows() if len(r["cells"]) < 5 or len(r["cells"][3]) < 10]
    assert not thin, (
        f"rows whose `what produced it` cell is empty or near-empty: {thin}. A "
        "finding with no source cannot be checked, and will be read as fact.")

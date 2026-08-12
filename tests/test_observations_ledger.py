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
SEEDED_ROWS = 17

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


# ---- 018 part 5: a retired UAT's findings must have a destination ---------
#
# The ledger has a trigger. A signed UAT sitting in christoph/done/ had none, so
# a finding written into one reached work only because the design session
# happened to be in the conversation -- three of 018's parts exist for exactly
# that reason, and nothing would have caught their absence.
#
# THE STRUCTURAL SHAPE WAS NOT AVAILABLE. A `**Findings**` section authored into
# each UAT is the better mechanism, and both 018's own Do-not list and CLAUDE.md
# forbid this session writing to christoph/ -- a check demanding a section it
# cannot add, to thirteen files it cannot edit, is red on arrival with no legal
# route to green. So the register keys on the LEDGER, which this side owns.
#
# ITS LIMIT, stated rather than discovered: it cannot detect a finding the
# reviewer overlooked. It forces someone to look and record that they looked.

UAT_DIR = REPO / "christoph" / "done"

REGISTER_ROW = re.compile(
    r"^\|\s*`(?P<uat>[^`]+\.md)`\s*\|\s*\*{0,2}(?P<status>[A-Z][A-Z ]*[A-Z])\*{0,2}\s*\|"
    r"(?P<rest>[^|]*)\|\s*(?P<review_by>[^|]*?)\s*\|\s*$", re.M)

UAT_STATUSES = ("CITED", "NO FINDINGS", "NOT REVIEWED")


def register() -> dict[str, dict]:
    if not LEDGER.exists():
        return {}
    out = {}
    for m in REGISTER_ROW.finditer(LEDGER.read_text(encoding="utf-8")):
        out[m.group("uat")] = {"status": m.group("status").strip(),
                               "note": m.group("rest").strip(),
                               "review_by": m.group("review_by").strip(" *")}
    return out


def retired_uats() -> list[str]:
    return sorted(p.name for p in UAT_DIR.glob("*.md")) if UAT_DIR.is_dir() else []


def unaccounted(uats: list[str], reg: dict) -> list[str]:
    """PURE, so Refusal B can be exercised without touching christoph/.

    018 forbids writing to or removing from that folder, so the fixture for
    'a retired UAT with a finding and no destination' is a synthetic name rather
    than a real file. The function under test is the same one the real check
    uses.
    """
    return [u for u in uats if u not in reg]


def test_every_retired_uat_has_a_register_row() -> None:
    """**The trigger.** A UAT retired into `christoph/done/` with no row here is
    a finding with nowhere to land, and that is the failure 018 part 5 names."""
    missing = unaccounted(retired_uats(), register())
    assert not missing, (
        "these retired UATs have no row in the UAT review register:\n  "
        + "\n  ".join(missing)
        + "\n\nA finding recorded in a retired UAT must land where something fails "
          "if it is\nignored. Add a row to the register in "
          "docs/observations/OBSERVATIONS.md:\n"
          "  CITED        -- name the OBS ids or task numbers it produced\n"
          "  NO FINDINGS  -- an assertion someone makes, with their name in git\n"
          "  NOT REVIEWED -- a declared backlog, and it needs a review-by date\n"
          "THIS SESSION MAY NOT WRITE TO christoph/. The row goes in the ledger.")


def test_every_register_status_is_one_of_the_three() -> None:
    wrong = [(u, r["status"]) for u, r in register().items()
             if r["status"] not in UAT_STATUSES]
    assert not wrong, f"register rows with a status outside {UAT_STATUSES}: {wrong}"


def test_a_cited_row_names_where_the_finding_went() -> None:
    """`CITED` is a claim that the findings were routed. A claim with no
    destination is a status field used as an off switch -- the same rule as
    PROMOTED needing a `resolution:`."""
    ids = {r["id"] for r in rows()}
    for uat, r in register().items():
        if r["status"] != "CITED":
            continue
        named = set(re.findall(r"OBS-\d{3}", r["note"]))
        assert named, f"{uat} is CITED but names no destination: {r['note']!r}"
        unknown = named - ids
        assert not unknown, (
            f"{uat} cites ledger rows that do not exist: {sorted(unknown)}")


def test_a_not_reviewed_row_is_not_overdue() -> None:
    """**Red for being ignored, not for being unreviewed.** A declared backlog is
    honest; a backlog past its own date is the thing this ledger exists to
    stop."""
    now = today()
    overdue = []
    for uat, r in register().items():
        if r["status"] != "NOT REVIEWED":
            continue
        d = parse_review_by(r["review_by"])
        assert d is not None, (
            f"{uat} is NOT REVIEWED with a missing or malformed review-by "
            f"({r['review_by']!r}). Unknown is never read as answered.")
        if d < now:
            overdue.append(f"{uat}  review-by {r['review_by']}  ({(now - d).days} days ago)")
    assert not overdue, (
        "these retired UATs have been unreviewed past their own date:\n  "
        + "\n  ".join(overdue)
        + "\n\nRead them and set CITED or NO FINDINGS, or move the date "
          "deliberately.")


def test_refusal_b_a_retired_uat_with_no_destination_is_red() -> None:
    """**Refusal B, exercised on synthetic input.**

    `018` forbids writing to or removing from `christoph/`, so the fixture is a
    UAT name rather than a UAT file. **The function is the one the real check
    calls**, so this is not a parallel implementation that could drift.
    """
    reg = register()
    fake = "099-a-uat-whose-findings-went-nowhere.md"
    missing = unaccounted(retired_uats() + [fake], reg)
    assert fake in missing, "a retired UAT with no register row was not caught"
    # And the message names it, which is what makes the red actionable.
    assert fake in "\n  ".join(missing)
    # The real folder is unchanged and still fully accounted for.
    assert not unaccounted(retired_uats(), reg)


def test_the_register_covers_the_uat_that_produced_this_mechanism() -> None:
    """`009` is why part 5 exists. Its three findings became 018 parts 2-4, and
    before this register nothing would have noticed if they had not."""
    reg = register()
    nine = [u for u in reg if u.startswith("009-")]
    assert nine, "009 is not in the register"
    assert reg[nine[0]]["status"] == "CITED"

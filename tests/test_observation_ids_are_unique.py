"""044 Part 3 — every `OBS-NNN` in the ledger is unique.

**This is the cheap half and it should have existed before any of this.** Same
shape as the `035` task-number collision one folder over, and the same fix:
**a number is read, never inferred as free.**

`tests/test_observations_ledger.py` checks staleness, resolutions and the UAT
register. **It never checked that an id names one finding.** Two sessions
allocated `OBS-044`, `OBS-045` and `OBS-046` on consecutive days and nothing went
red for two days.

----

**THIS TEST IS EXPECTED TO BE RED UNTIL CHRISTOPH RULES.** That is not an
oversight and it must not be silenced.

`044` Part 3 directs that duplicates be reallocated — *the earlier allocation
keeps the number, the later one is reallocated forward* — and its stated reason
is that `037` allocated `044`–`047` first, so moving the later rows breaks no
exported citation.

**Git says the opposite.** `e625df3` (2026-08-13 22:12, `021`'s rows) is an
ancestor of `eba938d` (2026-08-14 14:01, `037`'s rows). The `021` findings were
allocated first, so the literal rule reallocates the **`037`** rows — and those
are the meanings cited by **nine files under `handoff/`**, several already
exported to Drive.

`044` closes with an unconditional clause covering exactly this:

    If any reallocation would change what an exported done-note appears to have
    said, stop and report instead.

**It fires.** So `043`'s duplicates stand until Christoph chooses between the
rule and the reason it was given for. `handoff/questions/044-duplicate-ledger-ids.md`
holds the fork.

**Marking this `xfail` was considered and rejected.** An `xfail` removes it from
the failure count, which is the cheap route to green that
`test_observations_ledger.py`'s own docstring exists to warn about: *deleting a
row does not clear it.* A red test naming an unresolved defect is the ledger
convention working, not a broken suite.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LEDGER = REPO / "docs" / "observations" / "OBSERVATIONS.md"

#: A ledger row. Anchored to the row shape rather than to a bare `OBS-\d+`,
#: because ids are also *cited* in prose and in resolutions, and a citation is
#: not an allocation.
_ROW = re.compile(r"^\| \*\*(OBS-\d+)\*\* \| (\d{4}-\d{2}-\d{2}) \|", re.M)


def allocated_ids() -> list[tuple[str, str]]:
    """`(id, date)` for every ROW in the ledger, in file order."""
    return _ROW.findall(LEDGER.read_text(encoding="utf-8"))


def test_the_ledger_has_rows_at_all() -> None:
    """Guards the assertion below from passing on a parse that found nothing.

    A uniqueness check over an empty list is green, and this file's whole
    subject is a check that was absent — `OBS-037`'s shape.
    """
    rows = allocated_ids()
    assert len(rows) > 40, (
        f"only {len(rows)} ledger rows parsed out of {LEDGER}; the row regex "
        f"has probably drifted from the table format.")


def test_every_observation_id_is_allocated_once() -> None:
    rows = allocated_ids()
    counts = collections.Counter(i for i, _ in rows)
    dupes = {i: n for i, n in counts.items() if n > 1}

    detail = []
    for dup in sorted(dupes):
        dates = [d for i, d in rows if i == dup]
        detail.append(f"  {dup} x{dupes[dup]} — dated {', '.join(dates)}")

    assert not dupes, (
        "these ids each name more than one finding:\n" + "\n".join(detail)
        + "\n\n**A number is read, never inferred as free** — the same defect as "
          "the 035 task-number collision, one folder over.\n"
          "**This red is EXPECTED and is not yours to clear by renumbering.** "
          "044 Part 3's rule and the reason given for it point in opposite "
          "directions once git establishes the real order, and 044 says to stop "
          "and report rather than guess. See "
          "handoff/questions/044-duplicate-ledger-ids.md.")


def test_a_duplicate_would_be_caught() -> None:
    """**The guard, shown to fire, on text rather than on the live file.**

    044: *seen red by duplicating one.* Demonstrated here against a constructed
    table so that the demonstration does not depend on the live ledger being
    broken — which it currently is, and will not always be.
    """
    sample = (
        "| **OBS-001** | 2026-08-11 | OBSERVATION | a | b | c | OPEN | 2026-11-12 |\n"
        "| **OBS-002** | 2026-08-12 | OBSERVATION | a | b | c | OPEN | 2026-11-12 |\n"
        "| **OBS-001** | 2026-08-13 | OBSERVATION | a | b | c | OPEN | 2026-11-12 |\n"
    )
    found = _ROW.findall(sample)
    counts = collections.Counter(i for i, _ in found)
    assert [i for i, n in counts.items() if n > 1] == ["OBS-001"]

    clean = sample.replace("| **OBS-001** | 2026-08-13 |", "| **OBS-003** | 2026-08-13 |")
    counts = collections.Counter(i for i, _ in _ROW.findall(clean))
    assert not [i for i, n in counts.items() if n > 1]


def test_a_citation_is_not_counted_as_an_allocation() -> None:
    """`OBS-045` appears in prose all over the ledger's resolutions. **Only a
    table row allocates an id**, and counting citations would report every
    well-behaved cross-reference as a collision."""
    prose = (
        "**OBS-029 · DROPPED.**\n"
        "`resolution:` see OBS-001 and OBS-002, which supersede it.\n"
        "| **OBS-030** | 2026-08-13 | OBSERVATION | a | b | c | OPEN | 2026-11-12 |\n"
    )
    assert [i for i, _ in _ROW.findall(prose)] == ["OBS-030"]
